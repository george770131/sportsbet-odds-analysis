const path = require("path");
const projectRoot = path.resolve(__dirname, "..");

module.exports = {
  apps: [
    {
      name: "odds-collector",
      cwd: projectRoot,
      script: path.join(projectRoot, ".venv/bin/python"),
      args: "-m radar.collector --interval 120",
      interpreter: "none",
      autorestart: true,
      max_restarts: 50,
      restart_delay: 5000,
      env: {
        PYTHONUNBUFFERED: "1",
      },
    },
    {
      name: "odds-web",
      cwd: projectRoot,
      script: path.join(projectRoot, ".venv/bin/uvicorn"),
      args: "web.app:app --host 127.0.0.1 --port 8501",
      interpreter: "none",
      autorestart: true,
      max_restarts: 50,
      restart_delay: 3000,
      env: {
        PYTHONUNBUFFERED: "1",
      },
    },
    {
      name: "odds-tunnel",
      cwd: projectRoot,
      script: path.join(projectRoot, "deploy/run_tunnel_notify.sh"),
      interpreter: "bash",
      autorestart: true,
      max_restarts: 50,
      restart_delay: 5000,
      env: {
        RADAR_PORT: "8501",
      },
    },
  ],
};
