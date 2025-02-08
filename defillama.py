from dotenv import load_dotenv
from litellm import completion
import os
import json
import requests

load_dotenv()

## set ENV variables
#os.environ["OPENAI_API_KEY"] = "your-openai-key"
#os.environ["OPENROUTER_API_KEY"] = 

def get_llm_analysis(str):
    print("🔄 Getting LLM analysis...")
    messages = [{ "content": str,"role": "user"}, { "content": '''
You are a smart assistant designed to extract messages from a specific Telegram chat.

If the messages are not in English, you will translate them into English.
If asked to summarize messages, you will provide a summary.
If you receive a DeFi strategy message, you will conduct an in-depth analysis of potential DeFi investment options such as yield farming, liquidity pools, and staking.
Your analysis should return ONLY structured output with a summary of the strategy, tokens, potential risks, etc. in the following format:
"{ "Strategy": "[Strategy description]",  "StrategySteps": ["[Strategy description]"] "SmartContracts": ["[SmartContracts involved short name]"], "Tokens": ["[Tokens involved]"] "Rewards": "[Potential rewards]" "Risks": "[Potential risks]", "Compexity": "[Complexity level]", "CostConsiderations": "[Cost considerations]" }"
 ''',"role": "system"}]

    # openai call
    response = completion(
        model="openrouter/openai/gpt-4o",
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "investment_strategy_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "Strategy": {"type": "string", "description": "Strategy description"},
                        "StrategySteps": {"type": "array", "items": {"type": "string"}, "description": "Array of strategy steps"},
                        "SmartContracts": {"type": "array", "items": {"type": "string"}, "description": "Array of smart contracts involved short name single word only (e.g., USUAL)"},
                        "Tokens": {"type": "array", "items": {"type": "string"}, "description": "Array of tokens involved"},
                        "Rewards": {"type": "string", "description": "Potential rewards"},
                        "Risks": {"type": "string", "description": "Potential risks"},
                        "Complexity": {"type": "string", "description": "Complexity level"},
                        "CostConsiderations": {"type": "string", "description": "Cost considerations"}
                    },
                    "required": ["Strategy", "StrategySteps", "SmartContracts", "Tokens", "Rewards", "Risks", "Complexity", "CostConsiderations"]
                }
            }
        },
        messages=messages)
    #print(response)
    #print(response.choices[0].message.content)
    #response = completion(model="openrouter/deepseek/deepseek-chat", messages=messages)
    return json.loads(response.choices[0].message.content)

def get_defi_llama_data():
    print("🔄 Fetching data from DeFi Llama...")
    url = 'https://api.llama.fi/protocols'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def find_related_protocols(llm_data, defi_llama_data):
    smart_contracts = llm_data.get('SmartContracts', [])
    related_protocols = []
    
    for protocol in defi_llama_data:
        protocol_name = protocol.get('name', '').upper()
        for contract in smart_contracts:
            if contract.upper() in protocol_name:
                related_protocols.append(protocol)
                break
    
    tokens_tokens = llm_data.get('Tokens', [])
    
    for protocol in defi_llama_data:
        token_name = protocol.get('symbol', '').upper()
        for token in tokens_tokens:
            if token.upper() in token_name:
                related_protocols.append(protocol)
                break
    return related_protocols

def format_tvl(tvl):
    try:
        if tvl is None:
            return "N/A"
        return f"${float(tvl):,.2f}"
    except (ValueError, TypeError):
        return "N/A"

def analyze_protocols(smart_contracts, tokens, related_protocols):
    protocol_info = []
    for protocol in related_protocols:
        info = {
            'name': protocol.get('name', 'Unknown'),
            'symbol': protocol.get('symbol', 'Unknown'),
            'tvl': format_tvl(protocol.get('tvl')),
            'audits': protocol.get('audits', 'No audit information'),
            'audit_links': protocol.get('audit_links', []),
            'twitter': f"https://twitter.com/{protocol.get('twitter')}" if protocol.get('twitter') else "No Twitter handle"
        }
        protocol_info.append(info)
    
    # Create prompt for LLM
    messages = [{"content": f'''
Analyze the following protocols and select the best suited details for each smart contract in the list.
Smart Contracts: {smart_contracts}
Tokens: {tokens}
Protocol Details: {json.dumps(protocol_info, indent=2)}

Please provide a user-friendly summary including:
- TVL (Total Value Locked)
- Number of audits
- Audit links
- Twitter links
For each smart contract. In output don't use markdown
    ''', "role": "user"}, { "content": '''                 
In output don't use markdown
 ''' ,"role": "system"}]

    response = completion(model="openrouter/openai/gpt-4o", messages=messages)
    return response.choices[0].message.content

def combine_analysis(llm_data, protocol_analysis):
    messages = [{"content": f'''

Combine the following DeFi strategy information into a user-friendly summary:

Strategy Analysis:
{json.dumps(llm_data, indent=2)}

Protocol Analysis:
{protocol_analysis}

Please provide a comprehensive but easy-to-understand summary that combines both the strategy details
and the protocols' information. In output don't use markdown, but use the following blocks:
1. **Strategy tokens, protocols, overview**.
2. **Strategy steps**
3. **Expected rewards and timeframe**
4. **Protocols' security (TVL (set protocol grade base on the following TVL ranges:
$10B+		    Elite Protocols	Market leaders
$5B – $10B		Top Tier	
$1B – $5B		Mid-Level Protocols	
$500M – $1B		Emerging Players	Growing adoption, but limited market influence
$100M – $500M	Niche Protocols	Early-stage
Below $100M		Low Liquidity / Experimenta High risk
), audits links) and full links to twitter**
5. **Key risks, required actions/monitoring**
    ''', "role": "user"}]

    response = completion(model="openrouter/openai/gpt-4o", messages=messages)
    return response.choices[0].message.content

def convert_markdown_links(text):
    """Convert any markdown-style links to direct URLs."""
    import re
    pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    return re.sub(pattern, r'\2', text)

def process_invest_idea(investIdeaStr):
    # Step 1: Get LLM analysis
    llm_data = get_llm_analysis(investIdeaStr)
    print("Step 1 - LLM Analysis:", json.dumps(llm_data, indent=2))

    # Step 2: Get DeFi Llama data
    defi_llama_data = get_defi_llama_data()
    if not defi_llama_data:
        print("Failed to fetch DeFi Llama data")
        return

    # Step 3: Find related protocols
    related_protocols = find_related_protocols(llm_data, defi_llama_data)
    print("\nStep 3 - Related Protocols:", json.dumps([p.get('name', 'Unknown') for p in related_protocols], indent=2))

    # Step 4: Analyze protocols
    final_analysis = None
    if related_protocols:
        final_analysis = analyze_protocols(llm_data['SmartContracts'], llm_data['Tokens'], related_protocols[:10])
        print("\nStep 4 - Final Analysis:", final_analysis)
    else:
        print("No related protocols found")
        return

    # Step 5: Combine information into user-friendly format
    if final_analysis:
        user_friendly_summary = combine_analysis(llm_data, final_analysis)
        print("\nStep 5 - User-Friendly Summary:", user_friendly_summary)
        
        # Step 6: Convert markdown Twitter links to direct URLs
        converted_summary = convert_markdown_links(user_friendly_summary)
        print("\nStep 6 - Summary with Direct Links:", converted_summary)
        return converted_summary

if __name__ == "__main__":
    data = process_invest_idea('''
DeFi Investment Strategy Summary:\n- Divide digital dollars into 2 equal parts (50% each)\n- Buy USUAL token and short it on HyperLiquid DEX\n- Purchase PT (Principal Token) on USUALx via Pendle protocol\nPotential Returns: ~80% annually\nKey Points:\n- Position expires on 25 March 2025\n- Fixed PT income at current rate\n- 11% annual rate for USUAL short may fluctuate\nRisks:\n- Smart contract vulnerabilities\n- Insufficient collateral if USUAL price rises\nRecommendation: Carefully monitor position and collateral
     ''')
    print(data)
