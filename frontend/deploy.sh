#\!/bin/bash
echo "Starting deployment..."
cd frontend
echo "Installing dependencies..."
npm install
echo "Installing terser..."
npm install terser --save-dev
echo "Building project..."
npx vite build
echo "Build complete\!"
