

from  messagebird import Client

API_Key = 'VQYF6IzzCVqzI0xrow19YqdTL'

client = Client(API_Key)
message = client.message_create(
          'TestMessage',
          '31651827761',
          'This is a test message',
          { 'reference' : 'Foobar' }
      )
print (vars(message))