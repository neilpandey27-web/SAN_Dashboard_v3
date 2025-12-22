module.exports = {
  apps: [
    {
      name: 'backend',
      cwd: './backend',
      script: 'python3',
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload',
      interpreter: 'none',
      env: {
        PYTHONPATH: '/home/user/webapp/backend',
        NODE_ENV: 'development'
      },
      watch: false,
      instances: 1,
      exec_mode: 'fork'
    },
    {
      name: 'frontend',
      cwd: './frontend',
      script: 'npm',
      args: 'run dev',
      env: {
        NODE_ENV: 'development',
        PORT: 3000,
        NEXT_PUBLIC_API_URL: 'http://localhost:8000'
      },
      watch: false,
      instances: 1,
      exec_mode: 'fork'
    }
  ]
}
