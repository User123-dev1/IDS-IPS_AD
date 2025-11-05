#ifndef NETWORK_SCANNER_H
#define NETWORK_SCANNER_H

#include <string>
#include <vector>
#include <memory>
#include <functional>

struct ScanResult {
    std::string ip_address;
    std::string mac_address;
    std::string hostname;
    std::vector<int> open_ports;
    std::string device_type;
    std::string manufacturer;
    std::string protocol;
    float confidence;
    bool is_ot_device;
};

struct ScanConfig {
    std::string target_range;
    int timeout_ms = 5000;
    int max_threads = 50;
    bool deep_scan = false;
    bool protocol_detection = true;
    std::vector<int> custom_ports;
};

class NetworkScanner {
public:
    NetworkScanner();
    ~NetworkScanner();

    // Main scanning functions
    std::vector<ScanResult> scan_network(const ScanConfig& config);
    std::vector<ScanResult> scan_host(const std::string& ip, const ScanConfig& config);

    // Protocol-specific scanning
    bool detect_modbus(const std::string& ip, int port = 502);
    bool detect_opcua(const std::string& ip, int port = 4840);
    bool detect_ethernet_ip(const std::string& ip, int port = 44818);
    bool detect_dnp3(const std::string& ip, int port = 20000);

    // Security scanning
    std::vector<std::string> scan_vulnerabilities(const std::string& ip);
    bool check_default_credentials(const std::string& ip, const std::string& protocol);

    // Callbacks for progress reporting
    void set_progress_callback(std::function<void(int, const std::string&)> callback);
    void set_result_callback(std::function<void(const ScanResult&)> callback);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

#endif // NETWORK_SCANNER_H
