**A few useful commands to manage the app going forward:**



**# Restart the app**

docker compose restart orqagent



**# View app logs**

docker logs root-orqagent-1 --follow



**# Update after pushing new code to GitHub**

cd /var/www/orqagent

git pull

docker compose up -d --build orqagent



GROQ API KEY : gsk\_zQwkPtlvgH4ZoSkakpdWWGdyb3FY4ScMds7e7waPDLdhOAMB4P8K

