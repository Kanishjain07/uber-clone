# MongoDB Atlas Setup Guide

## 🔧 **Step 1: Get Your Atlas Connection String**

1. **Login to MongoDB Atlas**
   - Go to [cloud.mongodb.com](https://cloud.mongodb.com)
   - Sign in to your account

2. **Navigate to Your Cluster**
   - Click on your cluster name
   - Click the "Connect" button

3. **Choose Connection Method**
   - Select "Connect your application"
   - Choose "Python" as your driver
   - Select the appropriate version (4.x or later)

4. **Copy Connection String**
   - Your connection string will look like:
   ```
   mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority
   ```

## 🔑 **Step 2: Create Environment File**

Create a `.env` file in the backend directory:

```env
# Flask Configuration
SECRET_KEY=your-super-secret-key-here-change-this
JWT_SECRET_KEY=your-jwt-secret-key-here-change-this
FLASK_ENV=development

# MongoDB Atlas Configuration
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/uber_clone?retryWrites=true&w=majority

# Google Maps API
GOOGLE_MAPS_API_KEY=AIzaSyDqs1yX9nhlPP28-l062NeVEGV_9Ub9gYg

# Optional: Payment Configuration
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
```

## ⚠️ **Important Security Notes**

1. **Replace username and password** with your actual Atlas credentials
2. **Change the database name** from `uber_clone` to whatever you prefer
3. **Generate secure random keys** for SECRET_KEY and JWT_SECRET_KEY
4. **Never commit your .env file** to version control

## 🚀 **Step 3: Test Connection**

Once you have your `.env` file set up, test the connection:

```bash
python -c "from models.db import get_db; db = get_db(); print('✅ Connected to Atlas!')"
```

## 🔍 **Troubleshooting Atlas Issues**

### **Common Issues:**

1. **Network Access**
   - Ensure your IP address is whitelisted in Atlas
   - Or set `0.0.0.0/0` for development (not recommended for production)

2. **Authentication**
   - Verify username and password are correct
   - Check if your user has the right permissions

3. **Connection String Format**
   - Make sure you're using `mongodb+srv://` for Atlas
   - Verify the cluster name is correct

4. **Database Permissions**
   - Your Atlas user needs read/write permissions on the database

## 📊 **Atlas Dashboard Monitoring**

Once connected, you can monitor your application in Atlas:
- **Database Performance**: Check query performance
- **Connection Count**: Monitor active connections
- **Storage Usage**: Track database growth
- **Logs**: View connection and query logs

## 🎯 **Next Steps**

After setting up Atlas:
1. Create your `.env` file with the connection string
2. Test the connection
3. Run the backend: `python app.py`
4. Your app will automatically create the required collections and indexes

## 📞 **Need Help?**

- **Atlas Documentation**: [docs.atlas.mongodb.com](https://docs.atlas.mongodb.com)
- **Connection String Help**: [docs.mongodb.com/ecosystem/drivers/connection-string](https://docs.mongodb.com/ecosystem/drivers/connection-string)
- **Network Access**: [docs.atlas.mongodb.com/security/ip-access-list](https://docs.atlas.mongodb.com/security/ip-access-list)
