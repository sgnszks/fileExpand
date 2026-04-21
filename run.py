"""
应用启动入口

直接运行此文件即可启动开发服务器。
"""
from app.main import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
