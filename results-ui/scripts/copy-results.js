#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

// Copy results directory to api folder for Vercel serverless function
const sourceDir = path.join(__dirname, '..', '..', 'results');
const targetDir = path.join(__dirname, '..', 'results');

function copyRecursive(src, dest) {
  const exists = fs.existsSync(src);
  const stats = exists && fs.statSync(src);
  const isDirectory = exists && stats.isDirectory();
  
  if (isDirectory) {
    if (!fs.existsSync(dest)) {
      fs.mkdirSync(dest, { recursive: true });
    }
    fs.readdirSync(src).forEach(childItemName => {
      copyRecursive(
        path.join(src, childItemName),
        path.join(dest, childItemName)
      );
    });
  } else {
    fs.copyFileSync(src, dest);
  }
}

// Copy results directory if it exists
if (fs.existsSync(sourceDir)) {
  console.log('Copying results data for deployment...');
  copyRecursive(sourceDir, targetDir);
  console.log('Results data copied successfully');
} else {
  console.log('No results directory found, skipping...');
}

// Also copy data directory for quiz functionality
const dataSourceDir = path.join(__dirname, '..', '..', 'data');
const dataTargetDir = path.join(__dirname, '..', 'data');

if (fs.existsSync(dataSourceDir)) {
  console.log('Copying data files for deployment...');
  copyRecursive(dataSourceDir, dataTargetDir);
  console.log('Data files copied successfully');
} else {
  console.log('No data directory found, skipping...');
}