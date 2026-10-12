# Deployment Guide

## Local Deployment

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
copy .env.example .env
# Edit .env and add your API key (optional)
```

### 3. Test the Client
```bash
python api_example.py
```

## Docker Deployment

### Build and Run
```bash
docker-compose up --build
```

### Run Single Container
```bash
docker build -t macfax-client .
docker run --env-file .env macfax-client
```

## Production Deployment Options

### 1. AWS Lambda

Create `lambda_handler.py`:
```python
from macfax_client import MacfaxClient
import json

def lambda_handler(event, context):
    client = MacfaxClient()
    
    action = event.get('action')
    params = event.get('params', {})
    
    if action == 'lookup':
        result = client.lookup_serial(params['serial'])
    elif action == 'price_stats':
        result = client.get_price_stats(params['config'])
    elif action == 'listings':
        result = client.get_listings(params['config'])
    else:
        return {'statusCode': 400, 'body': 'Invalid action'}
    
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }
```

Deploy:
```bash
zip -r function.zip macfax_client.py config.py lambda_handler.py requirements.txt
aws lambda create-function --function-name macfax-api \
    --runtime python3.12 --handler lambda_handler.lambda_handler \
    --zip-file fileb://function.zip --role <YOUR_ROLE_ARN> \
    --environment Variables={MACFAX_API_KEY=your_key}
```

### 2. Google Cloud Functions

Create `main.py`:
```python
from macfax_client import MacfaxClient
import functions_framework

@functions_framework.http
def macfax_api(request):
    client = MacfaxClient()
    
    action = request.args.get('action')
    
    if action == 'lookup':
        serial = request.args.get('serial')
        result = client.lookup_serial(serial)
    elif action == 'price_stats':
        config = request.args.get('config')
        result = client.get_price_stats(config)
    else:
        return {'error': 'Invalid action'}, 400
    
    return result, 200
```

Deploy:
```bash
gcloud functions deploy macfax-api --runtime python312 \
    --trigger-http --allow-unauthenticated \
    --set-env-vars MACFAX_API_KEY=your_key
```

### 3. Azure Functions

Create `__init__.py`:
```python
import azure.functions as func
from macfax_client import MacfaxClient
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    client = MacfaxClient()
    
    action = req.params.get('action')
    
    if action == 'lookup':
        serial = req.params.get('serial')
        result = client.lookup_serial(serial)
    elif action == 'price_stats':
        config = req.params.get('config')
        result = client.get_price_stats(config)
    else:
        return func.HttpResponse("Invalid action", status_code=400)
    
    return func.HttpResponse(json.dumps(result), mimetype="application/json")
```

### 4. Heroku

Create `Procfile`:
```
web: python api_example.py
```

Deploy:
```bash
heroku create macfax-api-client
heroku config:set MACFAX_API_KEY=your_key
git push heroku main
```

### 5. Railway / Render / Fly.io

These platforms auto-detect Python apps. Just:
1. Connect your GitHub repo
2. Set environment variable `MACFAX_API_KEY`
3. Deploy

## Environment Variables

All deployment methods need:
```
MACFAX_API_KEY=mfx_your_key_here
MACFAX_BASE_URL=https://macfax.com/api/v1
MACFAX_TIMEOUT=30
```

## Security Best Practices

1. **Never commit `.env` file** - already in `.gitignore`
2. **Use secrets management** - AWS Secrets Manager, Azure Key Vault, etc.
3. **Rotate API keys** regularly
4. **Set request timeouts** - default 30s
5. **Monitor rate limits** - check response headers
6. **Log errors** - but not API keys

## Monitoring

Check API usage:
```python
client = MacfaxClient()
result = client.get_credits()
print(result['data'])
```

Monitor rate limits from response headers:
```python
result = client.lookup_serial("SERIAL")
headers = result['headers']
print(f"Remaining today: {headers.get('X-RateLimit-Remaining-Day')}")
```

## Scaling Considerations

- **Rate Limits**: Free key = 2000 lookups/day, Paid = 5000/day
- **Caching**: Cache resolved serials (they never change)
- **Batch Processing**: Use `bulk_lookup()` with proper delays
- **Error Recovery**: Client handles retries automatically
- **Cost**: 1 credit per distinct serial ($0.012-0.02 per lookup)

## Testing in Production

```bash
# Health check
curl https://macfax.com/api/v1/lookup?serial=C02P73J9G8WP

# With your deployment
curl https://your-deployment/lookup?serial=C02P73J9G8WP
```
