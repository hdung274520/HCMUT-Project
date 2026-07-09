# Tasks - JSON Schema & Parser Design (Multi-mode)

- `[x]` Update JSON Schema `medical_session_schema.json` to generalize stages to cognitive states
- `[x]` Update the parser code `parser_csv_to_json.py` to:
  - `[x]` Implement classification functions for Meditation, Focus, and Stress
  - `[x]` Compute overall scores, AI bullets, and alerts dynamically based on session type
  - `[x]` Transition layout from `sleep_stages` to generic `cognitive_states`
- `[x]` Update simulated data generator `generate_simulated_data.py` to generate data for specific session types
- `[x]` Update unit test suite `test_suite.py` to cover all 4 session types and validation paths
- `[x]` Execute the simulation, processing, and verification flow
- `[x]` Cập nhật `01_Pipeline.md` theo cấu trúc thư mục thực tế hiện tại
- `[x]` Cập nhật `README.md` đồng bộ hóa cấu trúc thư mục hệ thống
- `[x]` Khắc phục lỗi nhập biểu tượng Lucide (`CircleAlert`, `CircleCheck`) trong `page.js` của Web Dashboard
- `[x]` Thực hiện build kiểm thử ứng dụng Next.js để xác nhận biên dịch thành công
