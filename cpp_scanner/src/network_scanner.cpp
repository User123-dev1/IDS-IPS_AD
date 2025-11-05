#include "network_scanner.h"
#include "security_manager.h"
#include <thread>
#include <future>
#include <chrono>
#include <regex>
#include <iostream>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#include <iphlpapi.h>
#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "iphlpapi.lib")
#else
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#endif

class NetworkScanner::Impl {
public:
    SecurityManager security_manager;
    std::function<void(int, const std::string&)> progress_callback;
    std::function<void(const ScanResult&)> result_callback;

    std::vector<std::string> parse_ip_range(const std::string& range) {
        std::vector<std::string> ips;

        // Support CIDR notation (192.168.1.0/24)
        std::regex cidr_pattern(R"((\d{1,3}\.){3}\d{1,3}/\d{1,2})");
        if (std::regex_match(range, cidr_pattern)) {
            ips = expand_cidr_range(range);
        }
        // Support range notation (192.168.1.1-254)
        else if (range.find('-') != std::string::npos) {
            ips = expand_hyphen_range(range);
        }
        // Single IP
        else {
            ips.push_back(range);
        }

        return ips;
    }

    bool scan_tcp_port(const std::string& ip, int port, int timeout_ms) {
        struct sockaddr_in addr;
        addr.sin_family = AF_INET;
        addr.sin_port = htons(port);

#ifdef _WIN32
        addr.sin_addr.S_un.S_addr = inet_addr(ip.c_str());
#else
        inet_pton(AF_INET, ip.c_str(), &addr.sin_addr);
#endif

        int sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) return false;

        // Set non-blocking
#ifdef _WIN32
        u_long mode = 1;
        ioctlsocket(sock, FIONBIO, &mode);
#else
        int flags = fcntl(sock, F_GETFL, 0);
        fcntl(sock, F_SETFL, flags | O_NONBLOCK);
#endif

        // Attempt connection
        int result = connect(sock, (struct sockaddr*)&addr, sizeof(addr));

        if (result == 0) {
            // Connected immediately
#ifdef _WIN32
            closesocket(sock);
#else
            close(sock);
#endif
            return true;
        }

        // Wait for connection with timeout
        fd_set write_fds;
        FD_ZERO(&write_fds);
        FD_SET(sock, &write_fds);

        struct timeval timeout;
        timeout.tv_sec = timeout_ms / 1000;
        timeout.tv_usec = (timeout_ms % 1000) * 1000;

        result = select(sock + 1, nullptr, &write_fds, nullptr, &timeout);

#ifdef _WIN32
        closesocket(sock);
#else
        close(sock);
#endif

        return result > 0;
    }

private:
    std::vector<std::string> expand_cidr_range(const std::string& cidr) {
        // Implementation for CIDR expansion
        std::vector<std::string> ips;
        // ... CIDR parsing logic
        return ips;
    }

    std::vector<std::string> expand_hyphen_range(const std::string& range) {
        // Implementation for hyphen range expansion
        std::vector<std::string> ips;
        // ... Range parsing logic
        return ips;
    }
};

NetworkScanner::NetworkScanner() : pImpl(std::make_unique<Impl>()) {
#ifdef _WIN32
    WSADATA wsaData;
    WSAStartup(MAKEWORD(2, 2), &wsaData);
#endif
}

NetworkScanner::~NetworkScanner() {
#ifdef _WIN32
    WSACleanup();
#endif
}

std::vector<ScanResult> NetworkScanner::scan_network(const ScanConfig& config) {
    std::vector<ScanResult> results;
    auto target_ips = pImpl->parse_ip_range(config.target_range);

    // Validate scan authorization
    if (!pImpl->security_manager.is_scan_authorized(config.target_range)) {
        throw std::runtime_error("Unauthorized scan target: " + config.target_range);
    }

    std::atomic<int> completed_hosts{0};
    std::mutex results_mutex;

    // Thread pool for parallel scanning
    auto thread_count = std::min(config.max_threads, (int)target_ips.size());
    std::vector<std::future<void>> futures;

    for (int t = 0; t < thread_count; ++t) {
        futures.emplace_back(std::async(std::launch::async, [&, t]() {
            for (size_t i = t; i < target_ips.size(); i += thread_count) {
                auto result = scan_host(target_ips[i], config);

                if (!result.empty()) {
                    std::lock_guard<std::mutex> lock(results_mutex);
                    results.insert(results.end(), result.begin(), result.end());

                    if (pImpl->result_callback) {
                        for (const auto& r : result) {
                            pImpl->result_callback(r);
                        }
                    }
                }

                // Update progress
                int progress = (++completed_hosts * 100) / target_ips.size();
                if (pImpl->progress_callback) {
                    pImpl->progress_callback(progress, "Scanning " + target_ips[i]);
                }
            }
        }));
    }

    // Wait for completion
    for (auto& f : futures) {
        f.wait();
    }

    return results;
}

std::vector<ScanResult> NetworkScanner::scan_host(const std::string& ip, const ScanConfig& config) {
    std::vector<ScanResult> results;

    // Common OT ports to scan
    std::vector<int> ot_ports = {
        502,    // Modbus TCP
        4840,   // OPC-UA
        44818,  // EtherNet/IP
        20000,  // DNP3
        102,    // IEC 60870-5-104
        2404,   // IEC 61850 MMS
        1911,   // Tridium Fox
        4000,   // Wonderware
        9600    // BACnet
    };

    if (!config.custom_ports.empty()) {
        ot_ports = config.custom_ports;
    }

    ScanResult result;
    result.ip_address = ip;
    result.is_ot_device = false;

    // Scan ports
    for (int port : ot_ports) {
        if (pImpl->scan_tcp_port(ip, port, config.timeout_ms)) {
            result.open_ports.push_back(port);

            // Protocol detection
            if (config.protocol_detection) {
                if (port == 502 && detect_modbus(ip, port)) {
                    result.protocol = "Modbus TCP";
                    result.device_type = "PLC/RTU";
                    result.is_ot_device = true;
                    result.confidence = 0.9f;
                }
                else if (port == 4840 && detect_opcua(ip, port)) {
                    result.protocol = "OPC-UA";
                    result.device_type = "OPC Server";
                    result.is_ot_device = true;
                    result.confidence = 0.95f;
                }
                else if (port == 44818 && detect_ethernet_ip(ip, port)) {
                    result.protocol = "EtherNet/IP";
                    result.device_type = "Ethernet/IP Device";
                    result.is_ot_device = true;
                    result.confidence = 0.9f;
                }
            }
        }
    }

    if (!result.open_ports.empty()) {
        results.push_back(result);
    }

    return results;
}

bool NetworkScanner::detect_modbus(const std::string& ip, int port) {
    // Implement Modbus protocol detection
    // Send Modbus function code 03 (Read Holding Registers) request

    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) return false;

    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
#ifdef _WIN32
    addr.sin_addr.S_un.S_addr = inet_addr(ip.c_str());
#else
    inet_pton(AF_INET, ip.c_str(), &addr.sin_addr);
#endif

    if (connect(sock, (struct sockaddr*)&addr, sizeof(addr)) != 0) {
#ifdef _WIN32
        closesocket(sock);
#else
        close(sock);
#endif
        return false;
    }

    // Modbus TCP request: Read Holding Registers (FC=03)
    unsigned char modbus_request[] = {
        0x00, 0x01,  // Transaction ID
        0x00, 0x00,  // Protocol ID
        0x00, 0x06,  // Length
        0x01,        // Unit ID
        0x03,        // Function Code (Read Holding Registers)
        0x00, 0x00,  // Starting Address
        0x00, 0x01   // Quantity
    };

    send(sock, (char*)modbus_request, sizeof(modbus_request), 0);

    unsigned char response[256];
    int bytes_received = recv(sock, (char*)response, sizeof(response), 0);

#ifdef _WIN32
    closesocket(sock);
#else
    close(sock);
#endif

    // Check for valid Modbus response
    if (bytes_received >= 9 && response[6] == 0x01 && response[7] == 0x03) {
        return true;
    }

    return false;
}

void NetworkScanner::set_progress_callback(std::function<void(int, const std::string&)> callback) {
    pImpl->progress_callback = callback;
}

void NetworkScanner::set_result_callback(std::function<void(const ScanResult&)> callback) {
    pImpl->result_callback = callback;
}
