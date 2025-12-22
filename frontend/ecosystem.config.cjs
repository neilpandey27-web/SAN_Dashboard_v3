module.exports = {
  apps: [
    {
      name: 'storage-insights-frontend',
      script: 'node_modules/.bin/next',
      args: 'dev -p 3000',
      cwd: '/home/user/webapp/frontend',
      env: {
        NODE_ENV: 'development',
        NEXT_PUBLIC_API_URL: 'http://localhost:8000',
        PORT: 3000
      },
      watch: false,
      instances: 1,
      exec_mode: 'fork'
    }
  ]
}
