module.exports = {
  apps: [
    {
      name: 'storage-insights-backend',
      script: '/usr/local/bin/python',
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8000',
      cwd: '/home/user/webapp/backend',
      env: {
        PYTHONPATH: '/home/user/webapp/backend',
      },
      watch: false,
      instances: 1,
      exec_mode: 'fork'
    }
  ]
}
