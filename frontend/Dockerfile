# Dockerfile pour frontend
FROM node:20

WORKDIR /app

# Copier uniquement package.json pour installer les dépendances
COPY frontend/package*.json ./
RUN npm install

# Copier tout le reste du frontend
COPY frontend/ .

# Lancer le serveur
CMD ["npm", "start"]
