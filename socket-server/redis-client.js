const redis = require('redis');

class RedisClient {
  constructor() {
    this.subscriber = null;
    this.publisher = null;
  }

  async connect() {
    try {
      // Create Redis clients
      this.subscriber = redis.createClient({
        url: process.env.REDIS_URL || 'redis://localhost:6379'
      });

      this.publisher = redis.createClient({
        url: process.env.REDIS_URL || 'redis://localhost:6379'
      });

      // Connect both clients
      await this.subscriber.connect();
      await this.publisher.connect();

      console.log('✅ Redis connected successfully');
      return true;
    } catch (error) {
      console.error('❌ Redis connection error:', error);
      return false;
    }
  }

  getSubscriber() {
    return this.subscriber;
  }

  getPublisher() {
    return this.publisher;
  }

  async publish(channel, message) {
    await this.publisher.publish(channel, JSON.stringify(message));
  }

  async subscribe(channel, callback) {
    await this.subscriber.subscribe(channel, (message) => {
      try {
        const parsedMessage = JSON.parse(message);
        callback(parsedMessage);
      } catch (error) {
        console.error('Error parsing message:', error);
      }
    });
  }
}

module.exports = new RedisClient();