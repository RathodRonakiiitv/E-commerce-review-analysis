FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy application files
COPY . .

# Expose port
EXPOSE 3001

# Run development server
CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "3001"]
