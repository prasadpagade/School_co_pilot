# 🎨 Web UI Guide

## Accessing the UI

1. **Start the server** (if not already running):
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Open your browser** and navigate to:
   ```
   http://127.0.0.1:8000
   ```

3. **You'll see** a beautiful chat interface with:
   - Gradient purple background
   - Clean white chat container
   - Example questions to get started
   - Text input area for questions
   - Send button

## Using the UI

### Features

1. **Example Questions**
   - Click on any example question to auto-fill and send
   - Examples:
     - "What events are happening at school this week?"
     - "When is the next field trip?"
     - "What are the latest school announcements?"
     - "What is the dress code?"

2. **Ask Questions**
   - Type your question in the text area
   - Press `Enter` to send (or click the Send button)
   - Use `Shift + Enter` for a new line

3. **View Answers**
   - Answers appear in chat bubbles
   - User questions appear on the right (purple)
   - Assistant answers appear on the left (white)
   - Each message shows a timestamp

4. **Status Messages**
   - Green: Success messages
   - Red: Error messages
   - Status messages auto-hide after 3 seconds

### UI Features

- **Responsive Design**: Works on desktop and mobile
- **Auto-scroll**: Chat automatically scrolls to show new messages
- **Loading Indicator**: Shows "Thinking..." while processing
- **Error Handling**: Displays helpful error messages
- **Clean Interface**: Modern, gradient design

## Testing

### Quick Test

1. Open `http://127.0.0.1:8000` in your browser
2. Click on an example question or type your own
3. Wait for the response (usually 10-20 seconds)
4. View the answer in the chat

### Example Questions to Try

- "What events are happening at school this week?"
- "When is the next field trip?"
- "What are the latest school announcements?"
- "What is the dress code?"
- "When are parent-teacher conferences?"
- "What homework is due this week?"
- "What activities are scheduled for this month?"

## Troubleshooting

### UI Not Loading

1. **Check if server is running**:
   ```bash
   curl http://127.0.0.1:8000/health
   ```

2. **Restart the server**:
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Check browser console** (F12) for errors

### API Errors

- **429 Error**: Rate limit exceeded - wait a moment and try again
- **500 Error**: Server error - check server logs
- **Network Error**: Make sure the server is running on port 8000

### CORS Issues

- The UI includes CORS headers for local development
- If you see CORS errors, check that the server is running
- Make sure you're accessing `http://127.0.0.1:8000` (not `localhost`)

## UI Customization

The UI is in `static/index.html`. You can customize:

- **Colors**: Edit the CSS gradient colors
- **Layout**: Modify the container and chat styles
- **Features**: Add new functionality to the JavaScript
- **Examples**: Update the example questions

## Browser Compatibility

- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers

## Next Steps

1. **Test the UI**: Try asking different questions
2. **Customize**: Modify colors, layout, or features
3. **Deploy**: Consider deploying to a cloud service
4. **Share**: Share the UI with family members

## Screenshots

The UI features:
- Beautiful gradient background (purple/blue)
- Clean white chat container
- Message bubbles with timestamps
- Example questions for quick start
- Responsive design for all screen sizes

Enjoy testing your Denali School Copilot! 🚀

