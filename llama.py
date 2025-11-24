import requests

def llama(prompt):
    url = "http://127.0.0.1:1234/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    data = {
        "model": "local-llama",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        # Correct format for OpenAI-compatible API
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return ""
    
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to Llama server at http://127.0.0.1:1234")
        print("   Make sure your local LLM server is running")
        return ""
    except requests.exceptions.Timeout:
        print("❌ Error: Llama server timeout (took too long to respond)")
        return ""
    except Exception as e:
        print(f"❌ Error calling Llama: {str(e)}")
        return ""