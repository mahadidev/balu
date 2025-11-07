import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { email } = await request.json();

    if (!email || !email.includes('@')) {
      return NextResponse.json(
        { error: 'Valid email is required' },
        { status: 400 }
      );
    }

    // Store the subscription (you can add database logic here)
    console.log(`New subscription: ${email}`);

    // Send notification email to you
    await sendNotificationEmail(email);

    return NextResponse.json(
      { message: 'Successfully subscribed!' },
      { status: 200 }
    );
  } catch (error) {
    console.error('Subscription error:', error);
    return NextResponse.json(
      { error: 'Failed to subscribe' },
      { status: 500 }
    );
  }
}

async function sendNotificationEmail(subscriberEmail: string) {
  const nodemailer = require('nodemailer');

  // Configure with your email settings
  const transporter = nodemailer.createTransport({
    host: 'smtp.gmail.com',
    port: 587,
    secure: false,
    auth: {
      user: 'mahadi.dev.pm@gmail.com',
      pass: 'gdmn whgs mrnw dzqb',
    },
  });

  const mailOptions = {
    from: 'mahadi.dev.pm@gmail.com',
    to: 'mahadi.dev.pm@gmail.com', // Send to yourself
    subject: '🎉 New Balu Bot Newsletter Subscription!',
    html: `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #dc2626;">New Subscription Alert!</h2>
        <p>Someone just subscribed to the Balu Bot newsletter:</p>
        <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
          <strong>Email:</strong> ${subscriberEmail}<br>
          <strong>Time:</strong> ${new Date().toLocaleString()}<br>
          <strong>Source:</strong> Balu Bot Website
        </div>
        <p>You can reach out to them about bot updates and new features!</p>
        <hr>
        <p style="color: #666; font-size: 12px;">
          This notification was sent from your Balu Bot website subscription system.
        </p>
      </div>
    `,
  };

  try {
    await transporter.sendMail(mailOptions);
    console.log('Notification email sent successfully');
  } catch (error) {
    console.error('Failed to send notification email:', error);
    // Don't throw error - subscription should still work even if notification fails
  }
}