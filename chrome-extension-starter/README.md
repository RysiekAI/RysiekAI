# Chrome Extension Starter Template

This is a basic starter template for creating a Chrome extension using Manifest V3.

## Files

*   `manifest.json`: The core file that defines the extension's properties, permissions, and functionalities.
*   `popup.html`: The HTML file for the UI that appears when you click the extension icon in the Chrome toolbar.
*   `popup.js`: The JavaScript file to add interactivity to `popup.html`.
*   `popup.css`: The CSS file to style `popup.html`.
*   `icon.png`: A placeholder icon for the extension. You should replace this with your own icon (128x128 pixels is a good size).

## How to Load and Test

1.  **Open Chrome Extensions Page:**
    *   Open Google Chrome.
    *   Type `chrome://extensions` in the address bar and press Enter.

2.  **Enable Developer Mode:**
    *   In the top right corner of the Extensions page, you'll see a toggle switch for "Developer mode". Make sure it's turned ON.

3.  **Load Unpacked Extension:**
    *   Click the "Load unpacked" button that appears (usually on the top left).
    *   A file dialog will open. Navigate to this `chrome-extension-starter` directory (the one containing `manifest.json`) and select it.

4.  **Test the Extension:**
    *   Your extension should now appear in the list of installed extensions.
    *   It will also appear in the Chrome toolbar (you might need to click the puzzle piece icon to see it and then pin it).
    *   Click the extension icon in the toolbar. You should see the "Hello Extensions" message from `popup.html`.

5.  **Inspect the Popup (Optional):**
    *   To see console logs from `popup.js` or inspect the HTML/CSS of the popup:
        1.  Click the extension icon to open the popup.
        2.  Right-click anywhere inside the popup.
        3.  Select "Inspect". This will open Chrome DevTools for the popup.

## Next Steps

*   Customize `manifest.json` with your extension's name, description, and desired permissions.
*   Replace `icon.png` with your own icon.
*   Modify `popup.html`, `popup.js`, and `popup.css` to build your extension's user interface and functionality.
*   Explore the [Chrome Extension Documentation](https://developer.chrome.com/docs/extensions/mv3) for more advanced features like background scripts (service workers), content scripts, storage, etc.
