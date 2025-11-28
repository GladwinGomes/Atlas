import aiohttp
import asyncio

async def llama(prompt):
    url = "http://127.0.0.1:1234/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    data = {
        "model": "local-llama",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                response.raise_for_status()
                
                result = await response.json()
                
                # Correct format for OpenAI-compatible API
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    return ""
    
    except aiohttp.ClientConnectorError:
        print("❌ Error: Cannot connect to Llama server at http://127.0.0.1:1234")
        print("   Make sure your local LLM server is running")
        return ""
    except asyncio.TimeoutError:
        print("❌ Error: Llama server timeout (took too long to respond)")
        return ""
    except aiohttp.ClientError as e:
        print(f"❌ Error calling Llama: {str(e)}")
        return ""
    except Exception as e:
        print(f"❌ Error calling Llama: {str(e)}")
        return ""


# Example usage
async def main():
    result = await llama("Hello, how are you?")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())