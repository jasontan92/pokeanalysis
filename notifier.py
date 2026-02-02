"""
Telegram notification module for listing alerts.
Uses raw HTTP requests to Telegram Bot API.
"""

import requests
from typing import Optional
from config import Config


class TelegramNotifier:
    """Send notifications via Telegram Bot API."""

    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or Config.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or Config.TELEGRAM_CHAT_ID
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message to the configured chat.

        Args:
            text: Message text (can include HTML formatting)
            parse_mode: "HTML" or "Markdown"

        Returns:
            True if message was sent successfully
        """
        if not self.bot_token or not self.chat_id:
            print("Telegram not configured. Skipping notification.")
            return False

        url = f"{self.api_base}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                return True
            else:
                print(f"Telegram API error: {response.status_code} - {response.text}")
                return False
        except requests.RequestException as e:
            print(f"Failed to send Telegram message: {e}")
            return False

    def send_listing_alert(
        self,
        platform: str,
        title: str,
        price: Optional[float],
        link: str,
        listing_type: str = "NEW",
        time_left: str = None
    ) -> bool:
        """
        Send a formatted listing alert.

        Args:
            platform: "eBay" or "Fanatics"
            title: Listing title
            price: Price in USD (or None if not available)
            link: URL to the listing
            listing_type: "NEW" for new listing, "SOLD" for just sold, "ENDING" for ending soon
            time_left: Time remaining for auctions (optional)
        """
        if listing_type == "SOLD":
            emoji = "💰"
            header = f"JUST SOLD [{platform}]"
        elif listing_type == "ENDING":
            emoji = "🔥"
            header = f"ENDING SOON [{platform}]"
        else:
            emoji = "🆕"
            header = f"NEW LISTING [{platform}]"

        price_str = f"${price:,.2f}" if price else "Price not listed"

        message = (
            f"{emoji} <b>{header}</b>\n\n"
            f"📦 {title}\n"
            f"💵 {price_str}\n"
        )

        if time_left and listing_type == "ENDING":
            message += f"⏰ {time_left} left\n"

        message += f"🔗 <a href=\"{link}\">View Listing</a>"

        return self.send_message(message)

    def send_summary(self, new_count: int, sold_count: int) -> bool:
        """Send a summary of the monitoring run."""
        if new_count == 0 and sold_count == 0:
            return True  # Don't send empty summaries

        message = (
            f"📊 <b>Monitor Summary</b>\n\n"
            f"🆕 New listings: {new_count}\n"
            f"💰 Just sold: {sold_count}"
        )
        return self.send_message(message)

    def send_error(self, error_message: str) -> bool:
        """Send an error notification."""
        message = f"⚠️ <b>Monitor Error</b>\n\n{error_message}"
        return self.send_message(message)

    def test_connection(self) -> bool:
        """Test the Telegram bot connection."""
        url = f"{self.api_base}/getMe"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    bot_name = data["result"].get("username", "Unknown")
                    print(f"Telegram bot connected: @{bot_name}")
                    return True
            print(f"Telegram connection failed: {response.text}")
            return False
        except requests.RequestException as e:
            print(f"Telegram connection error: {e}")
            return False


# Convenience function for simple usage
def send_message(text: str) -> bool:
    """Send a message using default configuration."""
    notifier = TelegramNotifier()
    return notifier.send_message(text)


if __name__ == "__main__":
    # Test the notifier
    notifier = TelegramNotifier()

    if not Config.is_telegram_configured():
        print("Telegram not configured. Copy .env.example to .env and fill in values.")
    else:
        print("Testing Telegram connection...")
        if notifier.test_connection():
            print("Sending test message...")
            notifier.send_message("🤖 Test message from Pokemon listing monitor!")
            print("Done!")
