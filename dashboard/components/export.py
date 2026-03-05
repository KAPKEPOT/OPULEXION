# dashboard/components/export.py
"""
Export functionality for dashboard results
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import base64
import os
from pathlib import Path

def render_export_buttons():
    """Render export buttons for various formats"""
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("📊 CSV", use_container_width=True, help="Export as CSV"):
            export_as_csv()
    
    with col2:
        if st.button("📑 Excel", use_container_width=True, help="Export as Excel"):
            export_as_excel()
    
    with col3:
        if st.button("📄 PDF", use_container_width=True, help="Export as PDF"):
            export_as_pdf()
    
    with col4:
        if st.button("📧 Email", use_container_width=True, help="Send via email"):
            show_email_dialog()
    
    with col5:
        if st.button("🔗 API", use_container_width=True, help="Get API endpoint"):
            show_api_info()

def export_as_csv():
    """Export results as CSV"""
    
    # Create a buffer
    buffer = io.StringIO()
    
    # Get data
    if st.session_state.get('metrics_df') is not None:
        st.session_state.metrics_df.to_csv(buffer, index=True)
        
        # Download button
        st.download_button(
            label="📥 Download CSV",
            data=buffer.getvalue(),
            file_name=f"eiten_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key='csv_download'
        )

def export_as_excel():
    """Export results as Excel with multiple sheets"""
    
    # Create a buffer
    buffer = io.BytesIO()
    
    # Create Excel writer
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Metrics sheet
        if st.session_state.get('metrics_df') is not None:
            st.session_state.metrics_df.to_excel(writer, sheet_name='Performance Metrics')
        
        # Weights sheet
        if st.session_state.get('weights_df') is not None:
            st.session_state.weights_df.to_excel(writer, sheet_name='Portfolio Weights')
        
        # Returns sheet (if available)
        if st.session_state.get('returns_df') is not None:
            st.session_state.returns_df.to_excel(writer, sheet_name='Historical Returns')
        
        # Configuration sheet
        config_df = create_config_dataframe()
        config_df.to_excel(writer, sheet_name='Configuration', index=False)
    
    # Download button
    st.download_button(
        label="📥 Download Excel",
        data=buffer.getvalue(),
        file_name=f"eiten_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key='excel_download'
    )

def export_as_pdf():
    """Export results as PDF report"""
    
    st.info("📄 PDF export is being generated...")
    
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        import matplotlib.pyplot as plt
        
        # Create buffer
        buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1E88E5'),
            alignment=1,  # Center alignment
            spaceAfter=30
        )
        story.append(Paragraph("Eiten Portfolio Optimization Report", title_style))
        
        # Date
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.gray,
            alignment=2,  # Right alignment
            spaceAfter=20
        )
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style))
        
        story.append(Spacer(1, 20))
        
        # Configuration section
        story.append(Paragraph("Configuration", styles['Heading2']))
        config_data = [["Parameter", "Value"]]
        if st.session_state.get('stocks'):
            config_data.append(["Stocks", ", ".join(st.session_state.stocks[:5]) + 
                               ("..." if len(st.session_state.stocks) > 5 else "")])
        config_data.append(["Data Source", st.session_state.get('data_source', 'Yahoo Finance')])
        config_data.append(["Granularity", f"{st.session_state.get('granularity', 3600)} minutes"])
        config_data.append(["Test Size", f"{st.session_state.get('future_bars', 90)} bars"])
        config_data.append(["Eigen Portfolio #", st.session_state.get('eigen_number', 3)])
        config_data.append(["Market Index", st.session_state.get('market_index', 'QQQ')])
        config_data.append(["RMT Filtering", "Yes" if st.session_state.get('apply_filtering') else "No"])
        config_data.append(["Long Only", "Yes" if st.session_state.get('only_long') else "No"])
        
        config_table = Table(config_data, colWidths=[2*inch, 4*inch])
        config_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E88E5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(config_table)
        story.append(Spacer(1, 20))
        
        # Metrics section
        if st.session_state.get('metrics_df') is not None:
            story.append(Paragraph("Performance Metrics", styles['Heading2']))
            
            metrics_data = [["Strategy", "Sharpe", "Sortino", "Max DD", "Win Rate", "Alpha", "Beta"]]
            for strategy, row in st.session_state.metrics_df.iterrows():
                metrics_data.append([
                    strategy,
                    f"{row.get('Sharpe Ratio', 0):.2f}",
                    f"{row.get('Sortino Ratio', 0):.2f}",
                    f"{row.get('Max Drawdown', 0):.1f}%",
                    f"{row.get('Win Rate', 0):.1f}%",
                    f"{row.get('Alpha', 0):.3f}",
                    f"{row.get('Beta', 0):.2f}"
                ])
            
            metrics_table = Table(metrics_data, colWidths=[1.2*inch]*7)
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E88E5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(metrics_table)
            story.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(story)
        
        # Download button
        st.download_button(
            label="📥 Download PDF",
            data=buffer.getvalue(),
            file_name=f"eiten_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            key='pdf_download'
        )
        
    except ImportError:
        st.error("PDF export requires reportlab. Install with: pip install reportlab")
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")

def show_email_dialog():
    """Show email configuration dialog"""
    
    with st.form("email_form"):
        st.subheader("📧 Email Report")
        
        email = st.text_input("Email address", placeholder="your@email.com")
        include_attachments = st.checkbox("Include charts as attachments", True)
        
        col1, col2 = st.columns(2)
        with col1:
            send = st.form_submit_button("Send Report")
        with col2:
            cancel = st.form_submit_button("Cancel")
        
        if send:
            if email:
                st.success(f"✅ Report will be sent to {email}")
                # Here you would integrate with an email service
                # For now, just show success message
            else:
                st.error("Please enter a valid email address")

def show_api_info():
    """Show API endpoint information"""
    
    st.info("🔗 API Endpoint")
    st.code("""
    # Get results via API
    GET /api/v1/results
    GET /api/v1/metrics
    GET /api/v1/weights
    
    # Example using curl
    curl -X GET http://localhost:8000/api/v1/results
    
    # Example using Python
    import requests
    response = requests.get('http://localhost:8000/api/v1/metrics')
    data = response.json()
    """)
    
    # Show current results as JSON
    if st.session_state.get('metrics_df') is not None:
        st.json(st.session_state.metrics_df.to_dict())

def create_config_dataframe():
    """Create configuration dataframe for export"""
    
    config_data = {
        'Parameter': [
            'Timestamp',
            'Stocks',
            'Data Source',
            'Granularity',
            'Test Size',
            'Eigen Portfolio #',
            'Market Index',
            'RMT Filtering',
            'Long Only',
            'History'
        ],
        'Value': [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            str(len(st.session_state.get('stocks', []))),
            st.session_state.get('data_source', 'Yahoo Finance'),
            f"{st.session_state.get('granularity', 3600)} min",
            st.session_state.get('future_bars', 90),
            st.session_state.get('eigen_number', 3),
            st.session_state.get('market_index', 'QQQ'),
            'Yes' if st.session_state.get('apply_filtering') else 'No',
            'Yes' if st.session_state.get('only_long') else 'No',
            st.session_state.get('history', 'all')
        ]
    }
    
    return pd.DataFrame(config_data)