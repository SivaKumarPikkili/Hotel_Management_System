# Luxury Hotel Management System

A comprehensive hotel management system built with Flask, featuring room booking, admin dashboard, food ordering, and email notifications.

## Features

### ✅ Public Website
- View hotel overview, room types, image gallery, and contact info
- Allow users to check room availability via a calendar view
- Modern, responsive design with Bootstrap 5

### ✅ Room Booking System
- Visitors can browse room types and room numbers without logging in
- Login required only at the time of booking (not while browsing)
- Calendar shows booked and available dates per room
- Overlap protection prevents double bookings

### ✅ User Authentication
- User Register / Login / Logout system
- Password hashing for security
- Session-based login tracking
- Admin and regular user roles

### ✅ Booking System with Overlap Protection
- Book available rooms for a given date range
- Prevent overlapping bookings
- Users can view their own bookings
- Booking approval workflow

### ✅ Admin Dashboard
Admin can:
- Add/Edit/Delete room types and individual room numbers (e.g., Deluxe → 101, 102)
- Upload multiple images per room
- View full list of users and bookings
- Approve bookings via toggle
- Manage food menu items (for after-booking use)

### ✅ SQLite Database
Stores:
- Room types
- Room numbers (under each type)
- Room images (upload or URL)
- Bookings (with user, room, date range)
- Users
- Food orders

### 🖼️ Room Images (Upload + Display)
- Admin can upload multiple images using `<input type="file" multiple>`
- Store image paths in DB
- Show images in carousel or gallery per room
- Optionally allow adding external image URLs

### 🛏️ Room Types and Availability
- Support multiple rooms under the same category/type (e.g., Deluxe → 101, 102, 103)
- For each room:
  - Display room number (101, 102…)
  - Status: Booked / Available
  - Show status using colored badge/icons

### 📧 Booking Flow and Email Notifications
After a user books a room:
- Send booking email to the user
- Send approval request email to admin
- After admin approves (via toggle in dashboard):
  - Send confirmation email to user

### 🍽️ Food Ordering (Post Booking)
After booking is confirmed, unlock a food ordering section for the user:
- Visible only after confirmation
- Display menu with items and prices
- Allow user to select and place food orders for their room

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Hotel_Management
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   # Email Configuration (for notifications)
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   
   # Flask Configuration
   SECRET_KEY=your-secret-key-here-change-in-production
   FLASK_ENV=development
   ```

   **Note:** For Gmail, you'll need to:
   - Enable 2-factor authentication
   - Generate an App Password
   - Use the App Password in MAIL_PASSWORD

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open your browser and go to `http://localhost:5000`
   - Admin login: `admin` / `admin123`

## Database Structure

### Tables
- **User**: User accounts and authentication
- **RoomType**: Room categories (Deluxe, Standard, etc.)
- **Room**: Individual rooms with room numbers
- **RoomImage**: Multiple images per room
- **Booking**: Room reservations
- **FoodItem**: Menu items
- **FoodOrder**: Food orders linked to bookings

### Sample Data
The application comes with sample data:
- 4 room types (Deluxe Suite, Standard Room, Family Room, Executive Suite)
- 8 rooms (101, 102, 201, 202, 203, 301, 302, 401)
- 8 food items across different categories
- Admin user (admin/admin123)

## Usage

### For Guests
1. **Browse Rooms**: Visit the rooms page to see available room types
2. **Check Availability**: Use the calendar to check room availability
3. **Register/Login**: Create an account or login to book
4. **Book a Room**: Select dates and room, submit booking request
5. **Order Food**: After booking approval, order food for room service

### For Admins
1. **Dashboard**: View statistics and recent bookings
2. **Room Management**: Add/edit room types and individual rooms
3. **Booking Management**: Approve, cancel, or manage bookings
4. **User Management**: View and manage user accounts
5. **Food Menu**: Add/edit food items for room service

## File Structure

```
Hotel_Management/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .env                  # Environment variables (create this)
├── instance/
│   └── hotel.db         # SQLite database
├── static/
│   └── uploads/         # Uploaded images
└── templates/
    ├── base.html        # Base template
    ├── index.html       # Homepage
    ├── rooms.html       # Room listing
    ├── room_type_detail.html  # Room type details
    ├── book_room.html   # Booking form
    ├── my_bookings.html # User bookings
    ├── food_menu.html   # Food ordering
    ├── login.html       # Login form
    ├── register.html    # Registration form
    ├── gallery.html     # Image gallery
    ├── contact.html     # Contact page
    └── admin/           # Admin templates
        ├── dashboard.html
        ├── room_types.html
        ├── add_room_type.html
        ├── rooms.html
        ├── bookings.html
        ├── users.html
        └── food.html
```

## Features in Detail

### Room Management
- **Room Types**: Categories like "Deluxe Suite", "Standard Room"
- **Individual Rooms**: Specific room numbers under each type
- **Image Upload**: Multiple images per room with carousel display
- **Availability Tracking**: Real-time availability status

### Booking System
- **Date Range Selection**: Check-in and check-out dates
- **Overlap Prevention**: Automatic conflict detection
- **Approval Workflow**: Admin approval required
- **Email Notifications**: Automated email updates

### Food Ordering
- **Menu Categories**: Breakfast, Lunch, Dinner, Snacks
- **Order Management**: Quantity selection and special instructions
- **Status Tracking**: Pending, Preparing, Delivered
- **Booking Integration**: Only available for approved bookings

### Admin Features
- **Dashboard Analytics**: Revenue, bookings, user statistics
- **Room Management**: Add/edit room types and rooms
- **Booking Management**: Approve, cancel, view all bookings
- **User Management**: View users, manage admin privileges
- **Food Menu Management**: Add/edit menu items

## Security Features

- Password hashing using Werkzeug
- Session-based authentication
- Admin role protection
- Input validation and sanitization
- File upload restrictions

## Email Configuration

To enable email notifications:

1. **Gmail Setup**:
   - Enable 2-factor authentication
   - Generate App Password
   - Use App Password in .env file

2. **Other Providers**:
   - Update SMTP settings in app.py
   - Configure appropriate credentials

## Customization

### Adding New Features
- **Payment Integration**: Add payment gateway integration
- **Reviews System**: Guest reviews and ratings
- **Loyalty Program**: Points and rewards system
- **Multi-language**: Internationalization support

### Styling
- **Bootstrap 5**: Modern, responsive design
- **Custom CSS**: Easy to customize appearance
- **Font Awesome**: Icons throughout the interface

## Troubleshooting

### Common Issues

1. **Email not working**:
   - Check .env file configuration
   - Verify Gmail App Password
   - Check firewall/network settings

2. **Database errors**:
   - Delete instance/hotel.db to reset
   - Check file permissions

3. **Upload issues**:
   - Ensure static/uploads directory exists
   - Check file permissions
   - Verify file size limits

### Logs
- Check console output for error messages
- Flask debug mode provides detailed error information

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the code comments for implementation details

---

**Note**: This is a development version. For production use, ensure proper security measures, database backups, and SSL certificates are in place. 