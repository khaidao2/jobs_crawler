#!/bin/bash

# Khởi tạo dữ liệu cho Superset
superset db upgrade

# Tạo tài khoản Admin (Mặc định: admin / admin)
superset fab create-admin \
              --username admin \
              --firstname Superset \
              --lastname Admin \
              --email admin@superset.com \
              --password admin

# Khởi tạo các vai trò và quyền hạn
superset init

# Chạy server Superset
/usr/bin/run-server.sh
