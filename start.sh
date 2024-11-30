if command -v nvidia-smi &> /dev/null && nvidia-smi -L; then
  echo "GPU detected. Running GPU profile..."
  docker-compose --profile gpu up
else
  echo "No GPU detected. Running non-GPU profile..."
  docker-compose --profile non-gpu up
fi