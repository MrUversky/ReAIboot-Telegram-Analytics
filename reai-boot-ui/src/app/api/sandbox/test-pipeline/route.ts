import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    console.log('🔄 Next.js API Route: Forwarding request to backend');
    console.log('📦 Request body:', JSON.stringify(body, null, 2));

    const backendResponse = await fetch('http://localhost:8000/api/sandbox/test-pipeline', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    console.log('📨 Backend response status:', backendResponse.status);

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text();
      console.error('❌ Backend error:', errorText);
      return NextResponse.json(
        { error: 'Backend API error', details: errorText },
        { status: backendResponse.status }
      );
    }

    const data = await backendResponse.json();
    console.log('✅ Backend response data received');
    console.log('📊 Debug log length:', data.debug_log?.length);

    return NextResponse.json(data);
  } catch (error) {
    console.error('💥 Next.js API Route error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: (error as Error).message },
      { status: 500 }
    );
  }
}
