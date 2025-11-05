#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include "../include/network_scanner.h"
#include "../include/vulnerability_scanner.h"

namespace py = pybind11;

PYBIND11_MODULE(scanner_module, m) {
    m.doc() = "OT Asset Manager - Security-Critical Scanner Module";

    // ScanResult structure
    py::class_<ScanResult>(m, "ScanResult")
        .def(py::init<>())
        .def_readwrite("ip_address", &ScanResult::ip_address)
        .def_readwrite("mac_address", &ScanResult::mac_address)
        .def_readwrite("hostname", &ScanResult::hostname)
        .def_readwrite("open_ports", &ScanResult::open_ports)
        .def_readwrite("device_type", &ScanResult::device_type)
        .def_readwrite("manufacturer", &ScanResult::manufacturer)
        .def_readwrite("protocol", &ScanResult::protocol)
        .def_readwrite("confidence", &ScanResult::confidence)
        .def_readwrite("is_ot_device", &ScanResult::is_ot_device);

    // ScanConfig structure
    py::class_<ScanConfig>(m, "ScanConfig")
        .def(py::init<>())
        .def_readwrite("target_range", &ScanConfig::target_range)
        .def_readwrite("timeout_ms", &ScanConfig::timeout_ms)
        .def_readwrite("max_threads", &ScanConfig::max_threads)
        .def_readwrite("deep_scan", &ScanConfig::deep_scan)
        .def_readwrite("protocol_detection", &ScanConfig::protocol_detection)
        .def_readwrite("custom_ports", &ScanConfig::custom_ports);

    // NetworkScanner class
    py::class_<NetworkScanner>(m, "NetworkScanner")
        .def(py::init<>())
        .def("scan_network", &NetworkScanner::scan_network)
        .def("scan_host", &NetworkScanner::scan_host)
        .def("detect_modbus", &NetworkScanner::detect_modbus)
        .def("detect_opcua", &NetworkScanner::detect_opcua)
        .def("detect_ethernet_ip", &NetworkScanner::detect_ethernet_ip)
        .def("detect_dnp3", &NetworkScanner::detect_dnp3)
        .def("scan_vulnerabilities", &NetworkScanner::scan_vulnerabilities)
        .def("check_default_credentials", &NetworkScanner::check_default_credentials)
        .def("set_progress_callback", &NetworkScanner::set_progress_callback)
        .def("set_result_callback", &NetworkScanner::set_result_callback);
}
