const sgMail = require('@sendgrid/mail');

if (process.env.SENDGRID_API_KEY) {
  sgMail.setApiKey(process.env.SENDGRID_API_KEY);
}

async function sendWelcomeEmail(user) {
  if (!process.env.SENDGRID_API_KEY || !process.env.FROM_EMAIL) {
    console.warn('SendGrid not configured (SENDGRID_API_KEY/FROM_EMAIL missing) - skipping welcome email');
    return;
  }

  const msg = {
    to: user.email,
    from: process.env.FROM_EMAIL,
    subject: 'Welcome!',
    text: `Hi ${user.name}, your account has been created successfully.`,
    html: `<p>Hi ${user.name},</p><p>Your account has been created successfully.</p>`
  };

  try {
    await sgMail.send(msg);
  } catch (err) {
    console.error('Failed to send welcome email:', err.response?.body || err.message);
  }
}

module.exports = { sendWelcomeEmail };
