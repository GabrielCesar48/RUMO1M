# CLAUDE.md - AI Assistant Guide for RUMO1M

## Project Overview

**RUMO1M** (Journey to One Million) is a Django-based personal finance tracking application designed to help Brazilian users monitor their investment journey toward R$ 1,000,000. The application features inflation-adjusted value calculations using Brazil's IPCA (Índice de Preços ao Consumidor Amplo) and provides financial projections under multiple interest rate scenarios.

**Tech Stack:**
- Django 5.2.8 (Python web framework)
- SQLite3 (default database)
- Bootstrap 5.3 (frontend framework)
- Chart.js (data visualization)
- pandas & numpy (data processing)

**Current Branch:** `claude/claude-md-min9kfzvvyyo7znx-01U3NXZnXYSMFLwriYx7akwq`

## Repository Structure

```
RUMO1M/
├── config/                 # Django project settings
│   ├── settings.py        # Main configuration
│   ├── urls.py            # Root URL routing
│   └── wsgi.py            # WSGI configuration
├── dashboard/             # Main dashboard app
│   ├── views.py          # Dashboard logic and projections
│   ├── urls.py           # Dashboard URL routes
│   └── templates/        # Dashboard templates
├── investments/           # Investment management app (CORE)
│   ├── models.py         # Aporte (investment) model
│   ├── views.py          # CRUD operations for investments
│   ├── forms.py          # Investment forms
│   ├── urls.py           # Investment URL routes
│   ├── admin.py          # Admin interface configuration
│   └── services/         # Business logic services
│       ├── inflacao.py   # IPCA fetching and inflation correction
│       └── projecao.py   # Future value projection calculations
├── users/                 # User management (STUB - not implemented)
├── analytics/             # Analytics features (STUB - not implemented)
├── templates/             # Shared templates
│   ├── base.html         # Base template with Bootstrap
│   ├── dashboard/        # Dashboard-specific templates
│   ├── investments/      # Investment form templates
│   └── registration/     # Login/auth templates
├── manage.py              # Django management script
└── requirements.txt       # Python dependencies
```

## Core Application Logic

### Database Schema

**Primary Model: `Aporte` (investments/models.py)**

```python
class Aporte(models.Model):
    usuario = ForeignKey(User)          # Owner of investment
    data = DateField()                   # Investment date
    valor = DecimalField(10, 2)          # Original amount (BRL)
    valor_corrigido = DecimalField(12, 2) # Inflation-adjusted value
    descricao = CharField(100)           # Optional description
    criado_em = DateTimeField()          # Created timestamp

    ordering = ['data']  # Chronological order
```

### Key Business Logic Components

#### 1. Dashboard View (dashboard/views.py)

**Main Function: `dashboard(request)`**

Purpose: Display user's investment overview with statistics, projections, and badges.

Process Flow:
1. Fetch all user's investments ordered by date
2. Calculate statistics (total, count, average, max)
3. Build cumulative history array
4. Calculate achievement badges and progress
5. Generate 120-month projections under 3 scenarios:
   - Conservative: 8% annual return
   - Moderate: 12% annual return
   - Aggressive: 14% annual return
6. Suggest next investment amount (inflation-adjusted)

**Key Algorithm: `calcular_projecao(saldo_inicial, aporte_mensal, meses, taxa_anual)`**

```python
monthly_rate = (1 + annual_rate) ** (1/12) - 1
for each month:
    balance = balance * (1 + monthly_rate) + monthly_contribution
```

**Badge System: `calcular_badges(total)`**

21 progressive milestones from R$ 1,000 to R$ 1,000,000 with emoji indicators and progress tracking.

#### 2. Inflation Service (investments/services/inflacao.py)

**Critical Functions:**

- `buscar_ipca(ano, mes, tentativas_max=12)` - Fetches monthly IPCA from Brazilian Central Bank API
  - API: `https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados`
  - Validates returned data matches requested month/year
  - Implements retry logic with month fallback
  - Returns Decimal or None

- `fator_correção_ate(ano_inicio, mes_inicio, ano_ate, mes_ate)` - Calculates cumulative inflation factor
  - Applies IPCA month-by-month from start to end date
  - Returns Decimal multiplier

- `corrigir_historico(aportes, salvar=True)` - Corrects all historical investments
  - Calculates inflation from each investment date to current month
  - Optionally saves `valor_corrigido` to database

- `calcular_proximo_aporte(aportes)` - Suggests next investment value
  - Takes last investment amount and applies current IPCA

#### 3. Investment CRUD (investments/views.py)

Three main views:
- `adicionar_aporte()` - Create new investment
- `editar_aporte(request, pk)` - Update existing investment
- `deletar_aporte(request, pk)` - Delete investment

All views enforce user ownership via `usuario=request.user` filtering.

### URL Routing

```
/                             → Dashboard (login required)
/admin/                       → Django admin
/login/                       → Login page
/logout/                      → Logout
/investments/adicionar/       → Add investment
/investments/editar/<id>/     → Edit investment
/investments/deletar/<id>/    → Delete investment
```

## Development Conventions

### Language & Localization

- **Code comments:** Portuguese (BR)
- **Variable names:** Portuguese (e.g., `aporte`, `usuario`, `data`)
- **UI text:** Portuguese
- **Number formatting:** Brazilian (comma decimal separator, dot thousands)
- **Timezone:** America/Sao_Paulo
- **Currency:** Brazilian Real (R$)

### Code Style Guidelines

1. **Follow existing naming patterns:**
   - Use Portuguese variable names for domain models (`aporte`, `valor`, `data`)
   - Use English for technical terms (`request`, `response`, `form`)

2. **Model conventions:**
   - Always include `usuario` ForeignKey for user isolation
   - Use `DateField` for dates, `DecimalField` for currency
   - Add `verbose_name` and `verbose_name_plural` in Meta

3. **View conventions:**
   - Always use `@login_required` decorator
   - Filter querysets by `usuario=request.user`
   - Use `get_object_or_404()` for ownership verification
   - Redirect to dashboard with success messages after mutations

4. **Template conventions:**
   - Extend `base.html` for all pages (except login)
   - Use Bootstrap 5.3 classes
   - Apply border-radius: 20px to cards
   - Use green gradient theme (#10b981 to #059669)

5. **Service functions:**
   - Place complex business logic in `/services/` subdirectories
   - Use type hints where applicable
   - Return Decimal for financial calculations
   - Handle API failures gracefully (return None, don't raise)

### Testing Requirements

- Test files exist but are currently empty (`tests.py` in each app)
- When adding tests, use Django's `TestCase` class
- Test user isolation and ownership checks
- Mock external API calls (BCB IPCA endpoint)

### Security Best Practices

1. **User data isolation:** Always filter by `request.user`
2. **CSRF protection:** Use `{% csrf_token %}` in all forms
3. **Login enforcement:** Use `@login_required` on all non-public views
4. **Ownership verification:** Check `usuario` field before mutations
5. **Environment variables:** Use python-decouple for secrets

### Database Migrations

- Always create migrations for model changes: `python manage.py makemigrations`
- Review generated migration files before applying
- Apply migrations: `python manage.py migrate`
- Current migration state: Aporte with `valor_corrigido` field added in 0002

## Common Development Tasks

### Adding a New Investment Field

1. Modify `investments/models.py` - Add field to Aporte model
2. Create migration: `python manage.py makemigrations investments`
3. Apply migration: `python manage.py migrate`
4. Update `investments/forms.py` - Add field to AporteForm
5. Update templates to display new field
6. Update admin.py if field should appear in admin interface

### Adding a New Dashboard Metric

1. Modify `dashboard/views.py` - Add calculation in `dashboard()` function
2. Add metric to context dictionary
3. Update `templates/dashboard/home.html` to display metric
4. Consider adding to Chart.js visualization if time-series data

### Modifying Projection Logic

1. Edit `dashboard/views.py` - Modify `calcular_projecao()` function
2. Update projection calls with new parameters
3. Adjust Chart.js configuration in template if needed
4. Test with various scenarios (small/large balances, different timeframes)

### Adding New Badge Milestones

1. Edit `dashboard/views.py` - Modify `calcular_badges()` function
2. Add milestone to dictionary with threshold, emoji, and message
3. Ensure milestones are in ascending order
4. Test progress bar calculations

## External Dependencies

### Brazilian Central Bank API

**Endpoint:** `https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados`

**Purpose:** Fetch IPCA (inflation) data

**Parameters:**
- `formato=json`
- `dataInicial=01/MM/YYYY`
- `dataFinal=31/MM/YYYY`

**Response Format:**
```json
[
  {
    "data": "01/01/2024",
    "valor": "0.42"
  }
]
```

**Usage Notes:**
- 6-second timeout configured
- Retry logic with month fallback on failure
- Validate returned dates match requested period
- Data published monthly (usually mid-month for previous month)

## Environment Setup

### Required Environment Variables

```bash
SECRET_KEY=your-django-secret-key
DEBUG=False
```

### Installation Steps

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (for admin access)
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Database Configuration

**Default:** SQLite3 at `db.sqlite3`

**PostgreSQL Support:** Configured via settings, requires:
- Set DATABASE_URL environment variable
- psycopg2-binary already in requirements.txt

## Git Workflow

### Branch Strategy

- **Development branch:** `claude/claude-md-min9kfzvvyyo7znx-01U3NXZnXYSMFLwriYx7akwq`
- All changes should be committed to this branch
- Branch follows pattern: `claude/claude-md-{session-id}`

### Commit Guidelines

1. Write clear, descriptive commit messages in Portuguese
2. Use conventional commits where appropriate:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `refactor:` for code refactoring
   - `docs:` for documentation
3. Test changes before committing
4. Use `git add` selectively (don't commit unnecessary files)

### Push Instructions

```bash
# Push to development branch with upstream tracking
git push -u origin claude/claude-md-min9kfzvvyyo7znx-01U3NXZnXYSMFLwriYx7akwq

# Retry with exponential backoff on network errors (2s, 4s, 8s, 16s)
```

## Known Limitations & Technical Debt

1. **No Unit Tests:** Test files exist but are empty
2. **Magic Numbers:** Projection rates (8%, 12%, 14%) and badge thresholds hardcoded
3. **No Caching:** IPCA API calls could benefit from caching
4. **Limited Error Handling:** API failures return None but don't notify users
5. **Debug Statements:** Some print statements in production code
6. **No Transaction Handling:** Database operations lack transaction management
7. **Stub Apps:** Users and Analytics apps not implemented

## Future Enhancement Areas

### Stub Apps to Implement

- **Users App:** Custom user profiles, preferences, notification settings
- **Analytics App:** Detailed reports, data insights, trend analysis

### Potential Features

- CSV/PDF export of investment history
- Email notifications for milestones
- Custom goal setting (not just 1 million)
- Multi-currency support
- Advanced filtering and search
- REST API for mobile app integration
- Automated IPCA correction on scheduled basis
- Data visualization improvements (more chart types)

## Troubleshooting

### Common Issues

**IPCA API Returns None**
- Check if data is published yet (usually mid-month for previous month)
- Verify internet connection
- Check BCB API status
- Review timeout settings (currently 6 seconds)

**User Can't See Other Users' Investments**
- This is expected behavior (data isolation)
- Ensure `usuario=request.user` filter is present

**Projection Values Seem Wrong**
- Verify monthly rate calculation: `(1 + annual_rate) ** (1/12) - 1`
- Check that `saldo_inicial` is correctly passed
- Ensure `aporte_mensal` uses inflation-adjusted suggested value

**Badge Not Updating**
- Check threshold values in `calcular_badges()` function
- Verify total calculation includes all user's investments
- Ensure progress percentage calculation is correct

**Static Files Not Loading**
- Run `python manage.py collectstatic` for production
- Check STATIC_URL and STATIC_ROOT in settings.py
- Verify file paths in templates

## AI Assistant Guidelines

### When Working on This Codebase

1. **Always read existing code first** before making changes
2. **Maintain Portuguese naming** for domain concepts
3. **Preserve Brazilian localization** (date formats, currency, timezone)
4. **Test user isolation** - ensure changes don't leak data between users
5. **Follow existing patterns** - don't introduce new architectural styles
6. **Use Decimal for money** - never use float for currency
7. **Handle None gracefully** - services may return None on API failures
8. **Update migrations** after model changes
9. **Keep it simple** - avoid over-engineering
10. **Document in Portuguese** for consistency with existing comments

### Before Committing Code

- [ ] Tested manually in development environment
- [ ] No hardcoded secrets or credentials
- [ ] User isolation maintained (filter by `request.user`)
- [ ] CSRF token present in forms
- [ ] Migrations created and applied if models changed
- [ ] No unnecessary files added (e.g., `__pycache__`, `.pyc`)
- [ ] Code follows existing naming and style conventions
- [ ] Error handling present for external API calls

### Quick Reference Commands

```bash
# Run development server
python manage.py runserver

# Create migrations
python manage.py makemigrations [app_name]

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Open Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic

# Run tests (when implemented)
python manage.py test
```

## Key Files Quick Reference

| File | Purpose | Important Notes |
|------|---------|-----------------|
| `config/settings.py` | Django configuration | Contains localization, database, auth settings |
| `config/urls.py` | Root URL routing | Maps apps to URL paths |
| `dashboard/views.py` | Main dashboard logic | Contains projection and badge algorithms |
| `investments/models.py` | Aporte model | Core data model for investments |
| `investments/views.py` | Investment CRUD | User ownership verification critical |
| `investments/services/inflacao.py` | IPCA integration | External API calls, inflation calculations |
| `investments/forms.py` | Investment form | Form validation and widgets |
| `templates/base.html` | Base template | Bootstrap setup, navigation, messages |
| `templates/dashboard/home.html` | Dashboard UI | Chart.js visualization, stats cards |
| `requirements.txt` | Dependencies | 21 packages, pin versions for stability |

## Contact & Support

For questions about this codebase or development guidelines:
- Review this CLAUDE.md file
- Check Django documentation: https://docs.djangoproject.com/
- Check Bootstrap documentation: https://getbootstrap.com/docs/5.3/
- Check Chart.js documentation: https://www.chartjs.org/docs/

---

**Last Updated:** 2025-12-01
**Django Version:** 5.2.8
**Python Version:** 3.x (compatible)
**Database:** SQLite3 (default) / PostgreSQL (supported)
