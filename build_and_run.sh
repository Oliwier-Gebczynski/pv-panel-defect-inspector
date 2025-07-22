#!/bin/bash

# Configuration
BUILD_DIR="build"
EXECUTABLE_NAME="inspector"

echo "📁 Creating build directory (if it doesn't exist)..."
mkdir -p "$BUILD_DIR"

echo "🔧 Configuring the project with CMake..."
cmake -S . -B "$BUILD_DIR"

echo "🛠️  Building the project..."
cmake --build "$BUILD_DIR" -- -j$(nproc)

echo "🚀 Running the executable..."
"./$BUILD_DIR/$EXECUTABLE_NAME"