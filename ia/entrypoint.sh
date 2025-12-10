#!/bin/sh

# Iniciar el servidor Ollama en segundo plano
/bin/ollama serve &

# Esperar a que el servidor esté listo
sleep 5

# Descargar el modelo Gemma 3:1b automáticamente
ollama pull gemma2:2b

# Mantener el servidor en primer plano
wait
