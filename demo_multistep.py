#!/usr/bin/env python3
"""
Demo script showing multi-step function calling with mock data
This demonstrates the concept without requiring a real database
"""
import sys
import os

sys.path.append(".")


def demo_multistep_concept():
    """Demonstrate the multi-step concept with simulated data"""
    print("🎭 Multi-Step Function Calling Demonstration")
    print("=" * 60)
    print("This simulates how the agent would work with real data\n")

    # Simulate a multi-step customer lookup
    print("🔍 Scenario: 'Tell me everything about john.doe@example.com'")
    print("-" * 60)

    print("Step 1: get_customer_data('john.doe@example.com')")
    print("📄 Result: Found customer - John Doe, ID: 12345, Seattle, WA")

    print("\nStep 2: get_customer_details_by_email('john.doe@example.com')")
    print("📊 Executing sub-queries:")
    print("   2a. SELECT * FROM customer WHERE email = 'john.doe@example.com'")
    print(
        "   2b. SELECT customer_id FROM customer WHERE email = 'john.doe@example.com'"
    )
    print("   2c. SELECT sales data for customer_id = 12345")
    print("   2d. SELECT activity data for customer_id = 12345")

    print("\n📈 Combined Result:")
    print("   • Customer: John Doe, Premium Account, Seattle")
    print("   • Sales: 8 purchases, $3,200 total revenue")
    print("   • Activities: 12 support interactions, 5 product reviews")

    print("\n" + "=" * 60)

    # Simulate a multi-step product analysis
    print("\n🔍 Scenario: 'How is our CRM software performing?'")
    print("-" * 60)

    print("Step 1: get_product_data('CRM software')")
    print("📄 Result: Found CRM Professional v2.1, ID: 789, $299/month")

    print("\nStep 2: get_product_analytics('CRM software')")
    print("📊 Executing sub-queries:")
    print("   2a. SELECT * FROM product WHERE product_name LIKE '%CRM%'")
    print("   2b. SELECT sales analytics for product_id = 789")
    print("   2c. SELECT top customers for product_id = 789")
    print("   2d. SELECT activity stats for product_id = 789")

    print("\n📈 Combined Result:")
    print("   • Product: CRM Professional, 145 active subscriptions")
    print("   • Revenue: $43,355/month recurring, 23% growth")
    print("   • Top Customers: Enterprise Corp ($2,990), Tech Solutions ($1,495)")
    print("   • Engagement: 89% daily active users, 4.7/5 satisfaction")

    print("\n" + "=" * 60)

    # Show the function call sequence
    print("\n🔄 Agent's Internal Process")
    print("-" * 60)

    agent_process = """
    User: "Show me performance of CRM software and top customers"
    
    Agent Reasoning:
    Thought: I need product performance data and customer information.
    Action: get_product_data  
    Action Input: CRM software
    Observation: Found CRM Professional product, ID: 789
    
    Thought: Now I need detailed analytics for this product.
    Action: get_product_analytics
    Action Input: CRM software  
    Observation: Got comprehensive analytics including sales and customers
    
    Thought: I have all the information needed to provide a complete answer.
    Final Answer: [Comprehensive response with product performance and customer data]
    """

    print(agent_process)


def show_architecture_benefits():
    """Show the benefits of the multi-step architecture"""
    print("\n🏗️  Multi-Step Architecture Benefits")
    print("=" * 60)

    benefits = [
        {
            "benefit": "Comprehensive Data Gathering",
            "description": "Single query can collect data from multiple tables and sources",
            "example": "Customer profile + purchase history + support activities",
        },
        {
            "benefit": "Intelligent Query Sequencing",
            "description": "Uses results from one query to inform the next",
            "example": "Get customer ID first, then query sales using that ID",
        },
        {
            "benefit": "Contextual Analysis",
            "description": "Can correlate data across different business domains",
            "example": "Link support activity patterns to purchasing behavior",
        },
        {
            "benefit": "Flexible Response Depth",
            "description": "Adapts the number of function calls based on query complexity",
            "example": "Simple lookup = 1 call, deep analysis = 5+ calls",
        },
        {
            "benefit": "Error Recovery",
            "description": "If one data source fails, can try alternative approaches",
            "example": "Database unavailable → fallback to external search",
        },
    ]

    for i, benefit in enumerate(benefits, 1):
        print(f"\n{i}. {benefit['benefit']}")
        print(f"   📝 {benefit['description']}")
        print(f"   💡 Example: {benefit['example']}")


def show_real_world_examples():
    """Show real-world scenarios that benefit from multi-step calls"""
    print("\n🌍 Real-World Use Cases")
    print("=" * 60)

    scenarios = [
        {
            "query": "Which customers haven't purchased in 6 months but have high support activity?",
            "steps": [
                "1. Get all customers with recent support activities",
                "2. Check purchase history for each customer",
                "3. Filter customers with no recent purchases",
                "4. Correlate support activity with purchase patterns",
            ],
        },
        {
            "query": "What's the ROI of our premium support program?",
            "steps": [
                "1. Identify customers with premium support",
                "2. Calculate support costs per customer",
                "3. Analyze revenue from premium customers",
                "4. Compare retention rates vs standard customers",
            ],
        },
        {
            "query": "Show me our best product opportunity based on customer feedback",
            "steps": [
                "1. Analyze support ticket topics and sentiment",
                "2. Correlate with product usage patterns",
                "3. Identify feature gaps from customer activities",
                "4. Cross-reference with competitor research",
            ],
        },
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. Query: \"{scenario['query']}\"")
        print(f"   Multi-step approach:")
        for step in scenario["steps"]:
            print(f"      {step}")


if __name__ == "__main__":
    demo_multistep_concept()
    show_architecture_benefits()
    show_real_world_examples()

    print(f"\n🎉 Multi-Step Function Calling Demo Complete!")
    print("\nKey Takeaways:")
    print("✅ Agent can make 5-10 function calls in a single user interaction")
    print("✅ Each function call can inform and guide the next call")
    print("✅ Comprehensive data gathering across multiple business domains")
    print("✅ Intelligent reasoning about what information to collect")
    print("✅ Graceful handling of missing data or failed services")

    print("\nTo see this in action with real data:")
    print("1. Configure DATABASE_URL in .env file")
    print("2. Set up Ollama (http://localhost:11434) or Groq API")
    print("3. Run: python startup.py")
    print("4. Try complex queries in the Streamlit interface")
