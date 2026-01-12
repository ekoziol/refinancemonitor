# RefiAlert Email Layout & Formatting Standards

This document defines the design standards for all RefiAlert email communications.

## Brand Colors

| Color | Hex Code | Usage |
|-------|----------|-------|
| Primary Blue | `#22577A` | Headers, footer background, headings |
| Theme Blue | `#5eb9d7` | Accent color, links, CTAs, highlights |
| Header Gray | `#5f6988` | Subheadings, secondary text |
| Text Dark | `#333333` | Body text (primary) |
| Text Medium | `#555555` | Body text (secondary) |
| Text Light | `#888888` | Captions, fine print |
| Background | `#f4f4f4` | Email outer background |
| White | `#ffffff` | Content area background |
| Card Background | `#f8f9fa` | Details cards, info sections |

## Typography

| Element | Font | Size | Weight | Color |
|---------|------|------|--------|-------|
| Email Title | Poppins, system fonts | 28px | 600 | `#ffffff` |
| H2 Heading | Poppins, system fonts | 24px | 600 | `#22577A` |
| H3 Subheading | Poppins, system fonts | 18px | 600 | `#22577A` or `#5f6988` |
| Body Text | Poppins, system fonts | 16px | 400 | `#555555` |
| Small Text | Poppins, system fonts | 14px | 400 | `#666666` |
| Footer Text | Poppins, system fonts | 13px | 400 | `rgba(255,255,255,0.8)` |
| Fine Print | Poppins, system fonts | 12px | 400 | `rgba(255,255,255,0.6)` |

**Font Stack:** `'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif`

## Layout Structure

### Container
- Maximum width: **600px**
- Centered horizontally
- Outer background: `#f4f4f4`

### Header
- Background: Gradient from `#22577A` to `#5eb9d7` (135deg)
- Padding: 30px 40px
- Text alignment: Center
- Contains: Logo/brand name, tagline

### Content Area
- Background: `#ffffff`
- Padding: 40px
- Line height: 1.6

### Footer
- Background: `#22577A`
- Padding: 32px 40px
- Text alignment: Center
- Contains: Support links, copyright, unsubscribe

## Component Styles

### Alert Box (Warning)
```css
background-color: #fff3cd;
border-left: 4px solid #ffc107;
padding: 16px 20px;
border-radius: 0 4px 4px 0;
```

### Success Box
```css
background-color: #d4edda;
border-left: 4px solid #28a745;
padding: 16px 20px;
border-radius: 0 4px 4px 0;
```

### Info Box
```css
background-color: #e7f5fa;
border-left: 4px solid #5eb9d7;
padding: 16px 20px;
border-radius: 0 4px 4px 0;
```

### Details Card
```css
background-color: #f8f9fa;
padding: 24px;
border-radius: 8px;
border: 1px solid #e9ecef;
```

### Primary CTA Button
```css
background: linear-gradient(135deg, #5eb9d7 0%, #22577A 100%);
color: #ffffff;
padding: 14px 32px;
border-radius: 6px;
font-weight: 600;
font-size: 16px;
text-decoration: none;
```

### Secondary CTA Button
```css
background: transparent;
border: 2px solid #5eb9d7;
color: #5eb9d7;
padding: 14px 32px;
border-radius: 6px;
font-weight: 600;
font-size: 16px;
text-decoration: none;
```

### Divider
```css
border: 0;
border-top: 1px solid #e9ecef;
margin: 32px 0;
```

## Mobile Responsiveness

Breakpoint: **600px**

### Mobile Adjustments
| Element | Desktop | Mobile |
|---------|---------|--------|
| Header padding | 30px 40px | 24px 20px |
| Header title | 28px | 24px |
| Content padding | 40px | 24px 20px |
| H2 Heading | 24px | 20px |
| Footer padding | 32px 40px | 24px 20px |
| Card padding | 24px | 16px |
| CTA Button | inline-block | block, 100% width |

## Email Client Compatibility

### Supported Clients
- Gmail (Web, iOS, Android)
- Apple Mail (macOS, iOS)
- Outlook (365, 2019, 2016, Desktop)
- Yahoo Mail
- Outlook.com / Hotmail

### Compatibility Notes
1. Use table-based layout for maximum compatibility
2. Include inline styles (many clients strip `<style>` tags)
3. Use both `class` and inline `style` attributes
4. Include MSO conditional comments for Outlook
5. Use HTML entities for special characters in preheader
6. Always provide plain text alternative

## Template Variables

### Common Variables (all templates)
| Variable | Description |
|----------|-------------|
| `base_url` | Application base URL |
| `dashboard_url` | User dashboard URL |
| `unsubscribe_url` | Unsubscribe link |
| `preferences_url` | Email preferences URL |
| `current_year` | Current year for copyright |

### Alert Notification Variables
| Variable | Description |
|----------|-------------|
| `user_name` | User's display name |
| `mortgage_name` | Name of the mortgage |
| `alert_type` | Type of alert triggered |
| `trigger_reason` | Reason the alert was triggered |
| `trigger_date` | Date/time of trigger |
| `remaining_principal` | Current loan principal |
| `original_rate` | Current interest rate |
| `remaining_term` | Months remaining on loan |
| `target_monthly_payment` | Target monthly payment (optional) |
| `target_interest_rate` | Target interest rate (optional) |
| `target_term` | Target loan term in months |

### Payment Confirmation Variables
| Variable | Description |
|----------|-------------|
| `alert_id` | ID of the alert |
| `payment_status` | Status of payment (active, etc.) |
| `payment_date` | Date of payment |

## File Structure

```
templates/email/
├── base.html              # Base HTML template with header/footer
├── alert_notification.html # Alert triggered email
├── alert_notification.txt  # Plain text version
├── payment_confirmation.html # Payment success email
├── payment_confirmation.txt  # Plain text version
└── EMAIL_STANDARDS.md      # This document
```

## Usage Example

```python
from flask import render_template
from datetime import datetime

html_body = render_template(
    'email/alert_notification.html',
    user_name=user.name,
    mortgage_name=mortgage.name,
    alert_type=trigger.alert_type,
    # ... other variables
    base_url='https://refialert.com',
    dashboard_url='https://refialert.com/dashboard',
    unsubscribe_url='https://refialert.com/unsubscribe',
    preferences_url='https://refialert.com/preferences',
    current_year=datetime.now().year
)

text_body = render_template(
    'email/alert_notification.txt',
    # same variables
)
```

## Accessibility Guidelines

1. Maintain color contrast ratio of at least 4.5:1 for text
2. Use semantic heading hierarchy (H2, H3)
3. Include alt text for any images
4. Ensure links are descriptive
5. Provide plain text alternative for all emails

## Future Email Types

When adding new email templates, follow these patterns:

1. Extend `base.html`
2. Override relevant blocks: `title`, `preheader`, `header_icon`, `content`
3. Create matching `.txt` plain text version
4. Add template variables to this document
5. Use consistent component styles (alert-box, success-box, etc.)
