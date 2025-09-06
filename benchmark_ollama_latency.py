#!/usr/bin/env python3
"""
Latency benchmark test for GPT/OSS models via Ollama
"""

import requests
import time
import json
from datetime import datetime

def benchmark_ollama_model(model_name, test_prompts):
    """Benchmark a specific Ollama model"""
    
    print(f"\n🧪 Benchmarking: {model_name}")
    print("=" * 40)
    
    results = []
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n📝 Test {i}: {prompt[:50]}...")
        
        url = "http://localhost:11434/api/generate"
        data = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 100  # Limit response length for consistent timing
            }
        }
        
        try:
            # Measure total response time
            start_time = time.time()
            response = requests.post(url, json=data, timeout=60)
            end_time = time.time()
            
            total_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                
                # Calculate metrics
                tokens_generated = len(response_text.split())
                tokens_per_second = tokens_generated / total_time if total_time > 0 else 0
                
                print(f"  ⏱️  Total time: {total_time:.2f} seconds")
                print(f"  📊 Tokens generated: {tokens_generated}")
                print(f"  🚀 Tokens/second: {tokens_per_second:.1f}")
                print(f"  📄 Response: {response_text[:100]}...")
                
                results.append({
                    'prompt': prompt,
                    'total_time': total_time,
                    'tokens_generated': tokens_generated,
                    'tokens_per_second': tokens_per_second,
                    'success': True
                })
                
            else:
                print(f"  ❌ Request failed: {response.status_code}")
                results.append({
                    'prompt': prompt,
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                })
                
        except requests.exceptions.Timeout:
            print(f"  ⏰ Timeout after 60 seconds")
            results.append({
                'prompt': prompt,
                'success': False,
                'error': 'Timeout'
            })
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            results.append({
                'prompt': prompt,
                'success': False,
                'error': str(e)
            })
    
    return results

def test_cold_vs_warm_start(model_name):
    """Test cold start vs warm start performance"""
    
    print(f"\n🔥 Cold vs Warm Start Test: {model_name}")
    print("=" * 40)
    
    test_prompt = "Hello! Please respond with a brief greeting."
    
    # Test 1: Cold start (assuming model isn't loaded)
    print("\n❄️  Cold start test...")
    cold_start_time = time.time()
    
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model_name,
        "prompt": test_prompt,
        "stream": False,
        "options": {"num_predict": 50}
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        cold_end_time = time.time()
        cold_total_time = cold_end_time - cold_start_time
        
        if response.status_code == 200:
            print(f"  ⏱️  Cold start time: {cold_total_time:.2f} seconds")
        else:
            print(f"  ❌ Cold start failed: {response.status_code}")
            return
    except Exception as e:
        print(f"  ❌ Cold start error: {e}")
        return
    
    # Test 2: Warm start (model should now be loaded)
    print("\n🔥 Warm start test...")
    time.sleep(1)  # Brief pause
    
    warm_start_time = time.time()
    try:
        response = requests.post(url, json=data, timeout=30)
        warm_end_time = time.time()
        warm_total_time = warm_end_time - warm_start_time
        
        if response.status_code == 200:
            print(f"  ⏱️  Warm start time: {warm_total_time:.2f} seconds")
            
            # Compare
            improvement = ((cold_total_time - warm_total_time) / cold_total_time) * 100
            print(f"  📈 Improvement: {improvement:.1f}% faster")
        else:
            print(f"  ❌ Warm start failed: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Warm start error: {e}")

def check_available_models():
    """Check what models are available for testing"""
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return [model['name'] for model in models]
        else:
            return []
    except:
        return []

def main():
    """Run latency benchmarks"""
    
    print("⚡ GPT/OSS Model Latency Benchmark")
    print("=" * 50)
    print(f"🕐 Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if Ollama is running
    available_models = check_available_models()
    
    if not available_models:
        print("\n❌ No Ollama models found!")
        print("💡 Make sure:")
        print("  1. Ollama is installed and running (ollama serve)")
        print("  2. At least one model is downloaded (ollama pull llama3.2:1b)")
        return
    
    print(f"\n📦 Available models: {available_models}")
    
    # Test prompts of varying lengths
    test_prompts = [
        "Hello!",
        "What is artificial intelligence? Please explain briefly.",
        "Write a short customer service response for a billing inquiry about monthly charges.",
        "Explain the benefits of using local AI models versus cloud-based APIs for a business chatbot application, considering factors like privacy, cost, and performance."
    ]
    
    # Benchmark each available model
    all_results = {}
    
    for model in available_models:
        print(f"\n🚀 Testing model: {model}")
        
        # Basic performance test
        results = benchmark_ollama_model(model, test_prompts)
        all_results[model] = results
        
        # Cold vs warm start test
        test_cold_vs_warm_start(model)
        
        # Calculate averages for successful tests
        successful_results = [r for r in results if r.get('success')]
        if successful_results:
            avg_time = sum(r['total_time'] for r in successful_results) / len(successful_results)
            avg_tokens_per_sec = sum(r['tokens_per_second'] for r in successful_results) / len(successful_results)
            
            print(f"\n📊 {model} Summary:")
            print(f"  Average response time: {avg_time:.2f} seconds")
            print(f"  Average tokens/second: {avg_tokens_per_sec:.1f}")
    
    # Overall summary
    print("\n🎯 Benchmark Summary")
    print("=" * 30)
    
    for model, results in all_results.items():
        successful = len([r for r in results if r.get('success')])
        total = len(results)
        print(f"📈 {model}: {successful}/{total} tests successful")
    
    print("\n💡 Performance Tips:")
    print("  • Smaller models (1B-3B) = faster responses")
    print("  • GPU acceleration significantly improves speed")
    print("  • Keep models 'warm' by regular use")
    print("  • Shorter prompts = faster responses")
    print("  • Consider response length limits for consistent performance")

if __name__ == "__main__":
    main()
