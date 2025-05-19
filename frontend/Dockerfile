# Verwende Node.js als Basis-Image
FROM node:18-alpine AS base

# Installiere Abhängigkeiten für Sharp (für Bildverarbeitung falls benötigt)
RUN apk add --no-cache libc6-compat

# Stage 1: Dependencies installieren
FROM base AS deps
WORKDIR /app

# Kopiere package.json und package-lock.json
COPY frontend/package*.json ./

# Installiere Produktionsabhängigkeiten
RUN npm ci

# Stage 2: Build-Phase
FROM base AS builder
WORKDIR /app

# Kopiere die installierten Abhängigkeiten
COPY --from=deps /app/node_modules ./node_modules

# Kopiere Projektdateien
COPY frontend/ ./

# Umgebungsvariablen für Next.js als Build definieren
ENV NEXT_PUBLIC_API_URL=https://[DEINE-API-URL]

# Baue die Next.js-Anwendung
RUN npm run build

# Stage 3: Production-Image
FROM base AS runner
WORKDIR /app

# Setze umgebungsvariablen
ENV NODE_ENV=production

# Erstelle Benutzer für bessere Sicherheit
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Kopiere die Next.js Konfiguration
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Wechsele zum Benutzer mit weniger Rechten für bessere Sicherheit
USER nextjs

# Der Port, den Google Cloud Run erwartet
ENV PORT 8080
EXPOSE 8080

# Starte die Next.js-Anwendung
CMD ["node", "server.js"]
