import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
from typing import List, Dict, Any

# Configure the page
st.set_page_config(
    page_title="Test Data Analytics Dashboard", 
    page_icon="📊", 
    layout="wide"
)

# Generate sample data
@st.cache_data
def generate_sample_data():
    """Generate sample data for testing"""
    
    # Sample customers data
    customers = []
    cities = ['Seattle', 'Portland', 'San Francisco', 'Los Angeles', 'Denver', 'Austin', 'Chicago', 'New York']
    companies = ['TechCorp', 'DataSoft', 'CloudSys', 'WebDev Inc', 'AI Solutions', 'Digital Labs', 'Code Factory', 'InnoTech']
    
    for i in range(100):
        customer = {
            'id': f'CUST_{i+1:03d}',
            'name': f'Customer {i+1}',
            'email': f'customer{i+1}@{random.choice(companies).lower().replace(" ", "")}.com',
            'city': random.choice(cities),
            'company': random.choice(companies),
            'registration_date': datetime.now() - timedelta(days=random.randint(1, 365)),
            'total_orders': random.randint(0, 50),
            'total_spent': round(random.uniform(100, 10000), 2),
            'status': random.choice(['Active', 'Inactive', 'Premium', 'Trial'])
        }
        customers.append(customer)
    
    # Sample products data
    products = []
    categories = ['Software', 'Hardware', 'Services', 'Training', 'Support']
    product_names = [
        'Enterprise Suite', 'Analytics Pro', 'Cloud Storage', 'Security Shield',
        'Data Processor', 'Mobile App', 'Web Platform', 'API Gateway',
        'Database Engine', 'Monitoring Tool', 'Backup Solution', 'Integration Hub'
    ]
    
    for i, name in enumerate(product_names):
        product = {
            'id': f'PROD_{i+1:03d}',
            'name': name,
            'category': random.choice(categories),
            'price': round(random.uniform(50, 5000), 2),
            'stock': random.randint(0, 1000),
            'rating': round(random.uniform(3.0, 5.0), 1),
            'reviews_count': random.randint(10, 500),
            'created_date': datetime.now() - timedelta(days=random.randint(30, 730))
        }
        products.append(product)
    
    # Sample sales data
    sales = []
    for i in range(500):
        sale = {
            'id': f'SALE_{i+1:04d}',
            'customer_id': random.choice(customers)['id'],
            'product_id': random.choice(products)['id'],
            'quantity': random.randint(1, 10),
            'unit_price': round(random.uniform(50, 1000), 2),
            'total_amount': 0,  # Will calculate below
            'sale_date': datetime.now() - timedelta(days=random.randint(1, 90)),
            'status': random.choice(['Completed', 'Pending', 'Cancelled', 'Refunded']),
            'sales_rep': f'Rep {random.randint(1, 10)}'
        }
        sale['total_amount'] = round(sale['quantity'] * sale['unit_price'], 2)
        sales.append(sale)
    
    # Sample support tickets
    tickets = []
    priorities = ['Low', 'Medium', 'High', 'Critical']
    ticket_types = ['Bug', 'Feature Request', 'Support', 'Billing', 'Technical']
    statuses = ['Open', 'In Progress', 'Resolved', 'Closed']
    
    for i in range(200):
        ticket = {
            'id': f'TICK_{i+1:04d}',
            'customer_id': random.choice(customers)['id'],
            'title': f'Issue with {random.choice(product_names)}',
            'description': f'Customer reported an issue with {random.choice(["performance", "functionality", "installation", "configuration"])}',
            'priority': random.choice(priorities),
            'type': random.choice(ticket_types),
            'status': random.choice(statuses),
            'created_date': datetime.now() - timedelta(days=random.randint(1, 60)),
            'assigned_to': f'Agent {random.randint(1, 15)}'
        }
        tickets.append(ticket)
    
    return {
        'customers': pd.DataFrame(customers),
        'products': pd.DataFrame(products),
        'sales': pd.DataFrame(sales),
        'tickets': pd.DataFrame(tickets)
    }

def chatbot_response(user_input: str, data: Dict[str, pd.DataFrame]) -> str:
    """Simple chatbot that responds based on the user input and data"""
    
    user_input_lower = user_input.lower()
    
    # Customer-related queries
    if 'customer' in user_input_lower:
        if 'seattle' in user_input_lower:
            seattle_customers = data['customers'][data['customers']['city'] == 'Seattle']
            return f"Found {len(seattle_customers)} customers in Seattle:\n\n" + \
                   seattle_customers[['name', 'email', 'company', 'status']].to_string(index=False)
        
        elif 'count' in user_input_lower or 'how many' in user_input_lower:
            total_customers = len(data['customers'])
            active_customers = len(data['customers'][data['customers']['status'] == 'Active'])
            return f"Total customers: {total_customers}\nActive customers: {active_customers}"
        
        else:
            top_customers = data['customers'].nlargest(5, 'total_spent')[['name', 'company', 'total_spent']]
            return f"Top 5 customers by spending:\n\n" + top_customers.to_string(index=False)
    
    # Product-related queries
    elif 'product' in user_input_lower:
        if 'top' in user_input_lower or 'best' in user_input_lower:
            top_products = data['products'].nlargest(5, 'rating')[['name', 'category', 'price', 'rating']]
            return f"Top 5 rated products:\n\n" + top_products.to_string(index=False)
        
        elif 'software' in user_input_lower:
            software_products = data['products'][data['products']['category'] == 'Software']
            return f"Software products ({len(software_products)} total):\n\n" + \
                   software_products[['name', 'price', 'rating']].to_string(index=False)
        
        else:
            total_products = len(data['products'])
            avg_rating = data['products']['rating'].mean()
            return f"Total products: {total_products}\nAverage rating: {avg_rating:.2f}/5.0"
    
    # Sales-related queries
    elif 'sales' in user_input_lower:
        if 'today' in user_input_lower:
            today_sales = data['sales'][data['sales']['sale_date'].dt.date == datetime.now().date()]
            return f"Sales today: {len(today_sales)} transactions, Total: ${today_sales['total_amount'].sum():.2f}"
        
        elif 'total' in user_input_lower:
            total_sales = data['sales']['total_amount'].sum()
            completed_sales = data['sales'][data['sales']['status'] == 'Completed']['total_amount'].sum()
            return f"Total sales amount: ${total_sales:,.2f}\nCompleted sales: ${completed_sales:,.2f}"
        
        else:
            monthly_sales = data['sales'][data['sales']['sale_date'] >= datetime.now() - timedelta(days=30)]
            return f"Sales in last 30 days: {len(monthly_sales)} transactions, Total: ${monthly_sales['total_amount'].sum():.2f}"
    
    # Support ticket queries
    elif 'ticket' in user_input_lower or 'support' in user_input_lower:
        open_tickets = data['tickets'][data['tickets']['status'].isin(['Open', 'In Progress'])]
        critical_tickets = data['tickets'][data['tickets']['priority'] == 'Critical']
        return f"Support tickets summary:\n" + \
               f"Open/In Progress: {len(open_tickets)}\n" + \
               f"Critical priority: {len(critical_tickets)}\n" + \
               f"Total tickets: {len(data['tickets'])}"
    
    # Analytics queries
    elif 'analytics' in user_input_lower or 'report' in user_input_lower:
        return "📊 Analytics Summary:\n" + \
               f"• Total Customers: {len(data['customers'])}\n" + \
               f"• Total Products: {len(data['products'])}\n" + \
               f"• Total Sales: ${data['sales']['total_amount'].sum():,.2f}\n" + \
               f"• Average Order Value: ${data['sales']['total_amount'].mean():.2f}\n" + \
               f"• Open Support Tickets: {len(data['tickets'][data['tickets']['status'] == 'Open'])}"
    
    # Default response
    else:
        return f"I understand you're asking about: '{user_input}'\n\n" + \
               "I can help you with queries about:\n" + \
               "• Customers (e.g., 'Show customers from Seattle')\n" + \
               "• Products (e.g., 'Top rated products')\n" + \
               "• Sales (e.g., 'Sales this month')\n" + \
               "• Support tickets (e.g., 'Open tickets')\n" + \
               "• Analytics (e.g., 'Show analytics report')\n\n" + \
               "Try asking something like 'Show me top customers' or 'Sales analytics'!"

def main():
    """Main Streamlit application"""
    
    st.title("📊 Test Data Analytics Dashboard")
    st.markdown("Interactive dashboard with sample data for testing Streamlit functionality")
    
    # Generate sample data
    with st.spinner("Loading sample data..."):
        data = generate_sample_data()
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("Navigation")
        selected_tab = st.radio(
            "Select View",
            ["Dashboard", "Data Explorer", "Chatbot", "Analytics"]
        )
        
        st.header("Data Summary")
        st.metric("Customers", len(data['customers']))
        st.metric("Products", len(data['products']))
        st.metric("Sales", len(data['sales']))
        st.metric("Support Tickets", len(data['tickets']))
    
    if selected_tab == "Dashboard":
        st.header("📊 Dashboard Overview")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Customers", 
                len(data['customers']),
                delta=f"+{random.randint(5, 20)} this week"
            )
        
        with col2:
            total_sales = data['sales']['total_amount'].sum()
            st.metric(
                "Total Revenue", 
                f"${total_sales:,.0f}",
                delta=f"+{random.randint(10, 30)}% vs last month"
            )
        
        with col3:
            avg_rating = data['products']['rating'].mean()
            st.metric(
                "Avg Product Rating", 
                f"{avg_rating:.1f}/5.0",
                delta=f"+0.{random.randint(1, 3)}"
            )
        
        with col4:
            open_tickets = len(data['tickets'][data['tickets']['status'] == 'Open'])
            st.metric(
                "Open Tickets", 
                open_tickets,
                delta=f"-{random.randint(2, 8)}"
            )
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Sales by Date")
            daily_sales = data['sales'].groupby(data['sales']['sale_date'].dt.date)['total_amount'].sum().reset_index()
            daily_sales.columns = ['Date', 'Total Sales']
            fig = px.line(daily_sales, x='Date', y='Total Sales', title='Daily Sales Trend')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Customers by City")
            city_counts = data['customers']['city'].value_counts()
            fig = px.pie(values=city_counts.values, names=city_counts.index, title='Customer Distribution by City')
            st.plotly_chart(fig, use_container_width=True)
        
        # Product performance
        st.subheader("Product Performance")
        col1, col2 = st.columns(2)
        
        with col1:
            category_sales = data['products']['category'].value_counts()
            fig = px.bar(x=category_sales.index, y=category_sales.values, title='Products by Category')
            fig.update_xaxis(title='Category')
            fig.update_yaxis(title='Number of Products')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            ticket_status = data['tickets']['status'].value_counts()
            fig = px.donut(values=ticket_status.values, names=ticket_status.index, title='Support Ticket Status')
            st.plotly_chart(fig, use_container_width=True)
    
    elif selected_tab == "Data Explorer":
        st.header("🔍 Data Explorer")
        
        data_type = st.selectbox(
            "Select Data Type",
            ["Customers", "Products", "Sales", "Support Tickets"]
        )
        
        if data_type == "Customers":
            st.subheader("Customer Data")
            
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                city_filter = st.multiselect("Filter by City", data['customers']['city'].unique())
            with col2:
                status_filter = st.multiselect("Filter by Status", data['customers']['status'].unique())
            
            # Apply filters
            filtered_data = data['customers'].copy()
            if city_filter:
                filtered_data = filtered_data[filtered_data['city'].isin(city_filter)]
            if status_filter:
                filtered_data = filtered_data[filtered_data['status'].isin(status_filter)]
            
            st.dataframe(filtered_data, use_container_width=True)
            
            # Download option
            csv = filtered_data.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="customers.csv",
                mime="text/csv"
            )
        
        elif data_type == "Products":
            st.subheader("Product Data")
            
            # Filters
            category_filter = st.multiselect("Filter by Category", data['products']['category'].unique())
            price_range = st.slider("Price Range", 0, 5000, (0, 5000))
            
            # Apply filters
            filtered_data = data['products'].copy()
            if category_filter:
                filtered_data = filtered_data[filtered_data['category'].isin(category_filter)]
            filtered_data = filtered_data[
                (filtered_data['price'] >= price_range[0]) & 
                (filtered_data['price'] <= price_range[1])
            ]
            
            st.dataframe(filtered_data, use_container_width=True)
        
        elif data_type == "Sales":
            st.subheader("Sales Data")
            
            # Date range filter
            date_range = st.date_input(
                "Select Date Range",
                value=[datetime.now() - timedelta(days=30), datetime.now()],
                max_value=datetime.now()
            )
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                filtered_data = data['sales'][
                    (data['sales']['sale_date'].dt.date >= start_date) & 
                    (data['sales']['sale_date'].dt.date <= end_date)
                ]
                st.dataframe(filtered_data, use_container_width=True)
                
                # Summary metrics
                total_amount = filtered_data['total_amount'].sum()
                avg_order_value = filtered_data['total_amount'].mean()
                st.metric("Total Sales", f"${total_amount:,.2f}")
                st.metric("Average Order Value", f"${avg_order_value:.2f}")
        
        else:  # Support Tickets
            st.subheader("Support Tickets")
            
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                priority_filter = st.multiselect("Filter by Priority", data['tickets']['priority'].unique())
            with col2:
                status_filter = st.multiselect("Filter by Status", data['tickets']['status'].unique())
            
            # Apply filters
            filtered_data = data['tickets'].copy()
            if priority_filter:
                filtered_data = filtered_data[filtered_data['priority'].isin(priority_filter)]
            if status_filter:
                filtered_data = filtered_data[filtered_data['status'].isin(status_filter)]
            
            st.dataframe(filtered_data, use_container_width=True)
    
    elif selected_tab == "Chatbot":
        st.header("🤖 Interactive Chatbot")
        st.markdown("Ask questions about the sample data!")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "Hello! I can help you analyze the sample data. Try asking about customers, products, sales, or support tickets!"}
            ]
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask me about the data..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            
            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = chatbot_response(prompt, data)
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Sample queries
        st.subheader("💡 Try these sample queries:")
        sample_queries = [
            "Show me customers from Seattle",
            "What are the top-rated products?",
            "Show sales analytics",
            "How many open support tickets are there?",
            "Show software products",
            "Total revenue this month"
        ]
        
        for query in sample_queries:
            if st.button(query):
                st.session_state.messages.append({"role": "user", "content": query})
                response = chatbot_response(query, data)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
    
    else:  # Analytics
        st.header("📈 Advanced Analytics")
        
        # Time series analysis
        st.subheader("Sales Trend Analysis")
        
        # Aggregate sales by date
        daily_sales = data['sales'].groupby(data['sales']['sale_date'].dt.date).agg({
            'total_amount': 'sum',
            'id': 'count'
        }).reset_index()
        daily_sales.columns = ['Date', 'Revenue', 'Transaction Count']
        
        # Create dual-axis chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=daily_sales['Date'],
            y=daily_sales['Revenue'],
            name='Revenue',
            line=dict(color='blue')
        ))
        
        fig.add_trace(go.Scatter(
            x=daily_sales['Date'],
            y=daily_sales['Transaction Count'],
            name='Transaction Count',
            yaxis='y2',
            line=dict(color='red')
        ))
        
        fig.update_layout(
            title='Revenue and Transaction Trends',
            xaxis_title='Date',
            yaxis=dict(title='Revenue ($)', side='left'),
            yaxis2=dict(title='Transaction Count', side='right', overlaying='y'),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Correlation analysis
        st.subheader("Customer Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Customer spending vs orders
            fig = px.scatter(
                data['customers'], 
                x='total_orders', 
                y='total_spent',
                color='status',
                title='Customer Spending vs Order Count',
                labels={'total_orders': 'Number of Orders', 'total_spent': 'Total Spent ($)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Customer registration over time
            monthly_registrations = data['customers'].groupby(
                data['customers']['registration_date'].dt.to_period('M')
            ).size().reset_index()
            monthly_registrations.columns = ['Month', 'New Customers']
            monthly_registrations['Month'] = monthly_registrations['Month'].astype(str)
            
            fig = px.bar(
                monthly_registrations,
                x='Month',
                y='New Customers',
                title='Customer Registrations by Month'
            )
            fig.update_xaxis(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
