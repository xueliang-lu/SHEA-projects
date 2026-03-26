# Quick Reference - Student Risk Dashboard

Common tasks and troubleshooting for the Student Risk Analytics Dashboard.

---

## 🚀 Quick Start

```bash
# Activate environment
source venv/bin/activate

# Run dashboard
streamlit run apilog2.py
```

Default URL: `http://localhost:8501`

---

## 📊 Key Pages

| Page | Purpose |
|------|---------|
| **Dashboard** | Overview of all students, risk distribution |
| **Student Details** | Individual performance breakdown |
| **Email Outreach** | Send intervention emails |
| **Settings** | Configure weights, thresholds |

---

## ⚙️ Configuration

### Risk Thresholds (Default)

| Category | Risk Score | Triggers |
|----------|-----------|----------|
| **Critical** | > 75 | OR 3+ missed quizzes OR 2+ missed assignments |
| **Warning** | 50-75 | OR 1+ missed quiz OR 1+ missed assignment |
| **Safe** | < 50 | — |

### Risk Score Formula

```
Risk Score = 100 - (0.3 × Engagement + 0.4 × Completion + 0.3 × Performance)
```

- **Engagement (30%)**: Moodle activity (clicks + dwell time)
- **Completion (40%)**: Assessment submission rate
- **Performance (30%)**: Current weighted grade

---

## 📧 Email Setup

### Gmail App Password

1. Go to [Google Account](https://myaccount.google.com)
2. Security → 2-Step Verification → App passwords
3. Generate password for "Mail"
4. Use this password in `.env` file

### Test Email Connection

```python
# In Python console
import smtplib
server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
server.login('your_email@gmail.com', 'your_app_password')
print("Connection successful!")
```

---

## 🔧 Common Issues

### SSL Certificate Error (macOS)
```bash
/Applications/Python\ 3.13/Install\ Certificates.command
```

### Moodle Connection Fails
- Verify `MOODLE_URL` and `MOODLE_TOKEN` in `.env`
- Check Moodle Web Services are enabled
- Test token: `https://your-moodle.com/webservice/rest/server.php?wstoken=YOUR_TOKEN&moodlewsrestformat=json&wsfunction=core_webservice_get_site_info`

### No Data Showing
- Verify Course ID is correct
- Check Moodle logs are downloaded
- Ensure `studnet.csv` is in the correct format

### Port Already in Use
```bash
# Find process using port 8501
lsof -i :8501

# Kill process
kill -9 <PID>

# Or use different port
streamlit run apilog2.py --server.port 8502
```

---

## 📈 Best Practices

### For Coordinators

1. **Check dashboard weekly** - Catch at-risk students early
2. **Review Critical students first** - Highest priority for intervention
3. **Personalize emails** - Don't use generic templates
4. **Track outcomes** - Note which interventions work
5. **Update weights** - Adjust based on course structure

### Data Privacy

- ✅ Only access data for your courses
- ✅ Follow institutional privacy policies
- ✅ Don't share student data externally
- ✅ Secure your `.env` file
- ✅ Log out after each session

---

## 📞 Support

For technical issues, contact the system administrator.

---

**Last Updated:** March 2026
