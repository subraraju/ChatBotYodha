# Multi-Step Function Calling Architecture

## Overview
The chatbot agent now supports sophisticated multi-step function calling within a single user interaction. This means the agent can:

1. **Chain multiple function calls** in sequence to gather comprehensive information
2. **Use results from one function to inform the next** (e.g., get customer ID, then query sales with that ID)
3. **Break down complex queries** into smaller, manageable steps
4. **Provide step-by-step reasoning** about what information it's gathering

## How It Works

### Agent Configuration
The agent is configured with:
- **Max iterations: 10** - Allows for multiple function calls in one turn
- **Early stopping: "generate"** - Continues until a proper answer is generated
- **Enhanced prompting** - Encourages multi-step thinking

### Multi-Step Function Examples

#### 1. Customer Deep Dive
When a user asks: *"Tell me everything about customer john.doe@example.com"*

The agent will:
1. Call `get_customer_data("john.doe@example.com")` to find basic info
2. Extract customer ID from the result
3. Call `get_customer_details_by_email("john.doe@example.com")` for complete profile
4. Optionally call `get_sales_data()` for recent transactions
5. Synthesize all information into a comprehensive response

#### 2. Product Performance Analysis
When a user asks: *"How is our CRM software performing?"*

The agent will:
1. Call `get_product_data("CRM software")` to find the product
2. Call `get_product_analytics("CRM software")` for detailed performance
3. Call `get_sales_analytics()` for overall context
4. Possibly call `search_external_info("CRM best practices")` for benchmarking
5. Provide a complete performance analysis

#### 3. Complex Cross-Table Queries
When a user asks: *"Show me customers with high support activity and their purchase history"*

The agent will:
1. Call `get_activity_data("support")` to find support activities
2. Extract customer IDs from high-activity customers
3. Call `get_sales_data()` filtered by those customer IDs
4. Call `get_customer_data()` for customer details
5. Correlate the data and provide insights

## New Multi-Step Tools

### `get_customer_details_by_email(email)`
Performs a comprehensive customer lookup in multiple steps:
1. Gets basic customer information
2. Retrieves customer ID
3. Fetches all sales history for that customer
4. Fetches all activity history for that customer
5. Returns consolidated customer profile

### `get_product_analytics(product_name)`
Provides complete product analysis:
1. Finds product information
2. Calculates sales analytics (revenue, quantity, dates)
3. Identifies top customers for this product
4. Gathers activity/engagement statistics
5. Returns comprehensive product performance report

## Technical Implementation

### LangChain Agent Framework
```python
agent = initialize_agent(
    tools=self.tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    memory=self.memory,
    handle_parsing_errors=True,
    max_iterations=10,  # Allow multiple iterations
    early_stopping_method="generate",  # Continue until proper answer
)
```

### Enhanced Prompting
The system prompt now explicitly encourages multi-step thinking:
```
MULTI-STEP APPROACH:
1. If asked about a specific customer, first find their basic info, then get their complete details
2. If asked about product performance, get product info first, then detailed analytics  
3. For complex queries, break them down into smaller steps
4. Use the information from one function call to inform the next
5. Think step by step and explain your reasoning
```

## Function Call Flow Example

### User Query: "What can you tell me about john.doe@example.com and their purchases?"

#### Agent's Reasoning Process:
```
Thought: I need to get comprehensive information about this customer.
Action: get_customer_data
Action Input: john.doe@example.com

Observation: Found customer basic info - John Doe, ID: 123, Seattle, WA

Thought: Now I have the customer ID, let me get their complete details including sales.
Action: get_customer_details_by_email  
Action Input: john.doe@example.com

Observation: Complete customer profile with sales history - 5 purchases totaling $2,500

Thought: I should also check if there are any recent activities or support interactions.
Action: get_activity_data
Action Input: john

Observation: Found 3 support interactions and 2 product usage activities

Final Answer: [Comprehensive response combining all gathered information]
```

## Benefits of Multi-Step Architecture

1. **More Accurate Results** - Can gather precisely the right information through sequential queries
2. **Comprehensive Responses** - Provides complete context by combining multiple data sources  
3. **Flexible Query Handling** - Can adapt the function calling strategy based on user needs
4. **Transparent Process** - Shows step-by-step reasoning when verbose mode is enabled
5. **Error Recovery** - If one function fails, can try alternative approaches

## Testing Multi-Step Functionality

Run the comprehensive test:
```bash
python test_multistep_functions.py
```

This will demonstrate:
- Sequential function calls within single queries
- Using results from one function to inform the next
- Complex data gathering across multiple database tables
- Step-by-step reasoning and explanation

## Configuration

Ensure your `.env` file includes:
```env
DATABASE_URL=postgresql://username:password@server:5432/database
GROQ_API_KEY=your_groq_key  # or configure Ollama
TAVILY_API_KEY=your_tavily_key
```

The system gracefully handles missing services and provides informative error messages when databases or APIs are unavailable.
