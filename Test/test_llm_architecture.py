"""
Script de teste para validar a nova arquitetura LLM.
Testa tanto Gemini quanto Ollama e mostra a intercambiabilidade.
"""

import os
import sys
from dotenv import load_dotenv

# Adiciona o diretório da aplicação ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'App'))

# Carrega variáveis de ambiente
load_dotenv()

def test_llm_factory():
    """
    Testa a criação de modelos via Factory.
    """
    print("🧪 Testando LLM Factory...")
    
    try:
        from utils.llm_factory import LLMFactory, LLMProvider
        
        # Lista provedores disponíveis
        print("\n📋 Provedores disponíveis:")
        providers = LLMFactory.list_available_providers()
        for provider, available in providers.items():
            status = "✅ Disponível" if available else "❌ Indisponível"
            print(f"  • {provider}: {status}")
        
        # Testa criação de modelo SQL
        print("\n🔧 Testando criação de modelo SQL...")
        sql_model = LLMFactory.create_sql_model()
        print(f"  ✅ Modelo SQL criado: {sql_model.get_provider_name()}")
        
        # Testa criação de modelo Insights
        print("\n📊 Testando criação de modelo Insights...")
        insights_model = LLMFactory.create_insights_model()
        print(f"  ✅ Modelo Insights criado: {insights_model.get_provider_name()}")
        
        return sql_model, insights_model
        
    except Exception as e:
        print(f"❌ Erro no teste da Factory: {e}")
        return None, None

def test_compatibility():
    """
    Testa compatibilidade com código existente.
    """
    print("\n🔄 Testando compatibilidade com código existente...")
    
    try:
        from utils.llms import generative_model_sql, generative_model_insights, get_models_status
        from utils.llm_utils import safe_send_message
        
        # Mostra status dos modelos
        status = get_models_status()
        print(f"📊 Status dos modelos:")
        for model_name, model_status in status.items():
            if model_name != "available_providers":
                print(f"  • {model_name}: {model_status}")
        
        # Testa se os modelos foram carregados
        if generative_model_sql:
            print(f"  ✅ Modelo SQL disponível: {generative_model_sql.get_provider_name()}")
        else:
            print("  ❌ Modelo SQL não disponível")
            
        if generative_model_insights:
            print(f"  ✅ Modelo Insights disponível: {generative_model_insights.get_provider_name()}")
        else:
            print("  ❌ Modelo Insights não disponível")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de compatibilidade: {e}")
        return False

def test_simple_generation():
    """
    Testa geração simples de conteúdo.
    """
    print("\n🚀 Testando geração de conteúdo...")
    
    try:
        from utils.llms import generative_model_sql
        from utils.llm_utils import safe_send_message
        
        if not generative_model_sql:
            print("❌ Modelo SQL não disponível para teste")
            return False
        
        # Teste simples
        prompt = "Diga 'Teste funcionando' em uma frase."
        
        print(f"📝 Enviando prompt: {prompt}")
        response = safe_send_message(generative_model_sql, prompt)
        
        if response and hasattr(response, 'text'):
            print(f"✅ Resposta recebida: {response.text[:100]}...")
            return True
        else:
            print("❌ Resposta inválida recebida")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de geração: {e}")
        return False

def test_provider_switching():
    """
    Testa mudança de provedor via variável de ambiente.
    """
    print("\n🔄 Testando mudança de provedores...")
    
    try:
        from utils.llm_factory import LLMFactory, LLMProvider
        
        # Lista provedores disponíveis
        providers = LLMFactory.list_available_providers()
        available_providers = [p for p, available in providers.items() if available]
        
        if len(available_providers) < 2:
            print("⚠️  Apenas um provedor disponível, não é possível testar mudança")
            return True
        
        # Testa criação com diferentes provedores
        for provider_name in available_providers:
            provider = LLMProvider(provider_name)
            model = LLMFactory.create_sql_model(provider=provider)
            print(f"  ✅ Modelo criado com {provider_name}: {model.get_provider_name()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de mudança de provedores: {e}")
        return False

def main():
    """
    Executa todos os testes.
    """
    print("🎯 Iniciando testes da nova arquitetura LLM")
    print("=" * 50)
    
    # Mostra configuração atual
    provider = os.environ.get("LLM_PROVIDER", "gemini")
    print(f"🔧 Provedor configurado: {provider}")
    
    # Executa testes
    tests = [
        ("Factory Pattern", test_llm_factory),
        ("Compatibilidade", test_compatibility),
        ("Geração Simples", test_simple_generation),
        ("Mudança de Provedores", test_provider_switching)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro crítico em {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo dos resultados
    print(f"\n{'='*20} RESUMO {'='*20}")
    passed = 0
    for test_name, result in results:
        if result:
            print(f"✅ {test_name}: PASSOU")
            passed += 1
        else:
            print(f"❌ {test_name}: FALHOU")
    
    print(f"\n📊 Resultado final: {passed}/{len(tests)} testes passaram")
    
    if passed == len(tests):
        print("🎉 Todos os testes passaram! A nova arquitetura está funcionando.")
    else:
        print("⚠️  Alguns testes falharam. Verifique a configuração.")

if __name__ == "__main__":
    main()
