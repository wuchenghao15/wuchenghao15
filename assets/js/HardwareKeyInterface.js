// VERSION: 20251106.33ac9757b1cc0f0dfa1

function HardwareKeySocketInterface()
{
	var u = document.URL;
    var url;
    var strSocketResult = '';
    if (u.substring(0, 5) == "https") 
	{
		url = "ws://localhost:8189";
	}
	else 
	{
		url = "ws://localhost:8189";
	}
    
    var HardwareKeySocket;
	if (typeof MozWebSocket != "undefined") 
	{
		this.HardwareKeySocket = new MozWebSocket(url);
	} 
	else 
	{
		this.HardwareKeySocket = new WebSocket(url);
	}
		
	Initialize = function() 
	{ 
		try
		{
			this.FindHardwareKey();	
			//this.GetVersion();
			//this.GetVersion();
			return true;
		}
		catch(exception)
		{
			
		}
		
		return false;
	};   
	this.GetVersion = function() 
	{
		try
		{
			var msg = 
			{
				FunctionType: "GetVersion",
				start: "start"
			};

			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;		
			
		}	
		catch(exception)
		{
			OutputLog('Error'+exception);
		}
		
		return false;		
	};
	
	this.CheckInstall = function() 
	{
		try
		{
			var msg = 
			{
				FunctionType: "CheckInstall",
				start: "start"
			};

			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			//this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;		
			
		}	
		catch(exception)
		{
			OutputLog('Error'+exception);
		}
		
		return false;		
	};
	this.FindHardwareKey = function() 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeyFind",
				start: "start"
			};

			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;		
			
		}	
		catch(exception)
		{
			OutputLog('Error'+exception);
		}
		
		return false;		
	};
	
    this.HardwareKeyGetHID = function(index) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeyGetHID",
				Index: index
			};
	
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
			
		}
		
		return false;
	};
	
    this.HardwareKeyGetType = function(index) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeyGetType",
				Index: index
			};
	
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
			
		}
		
		return false;
	};
	
    this.HardwareKeyGetLevel = function(index) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeyGetLevel",
				Index: index
			};
	
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
			
		}
		
		return false;
	};
	
    this.HardwareKeyGetPtroductName = function(index) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeyGetPtroductName",
				Index: index
			};
	
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
			
		}
		
		return false;
	};
	
    this.HardwareKeyUserLogin = function(index, UserPw) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeyUserLogin",
				Index: index,
				UserPw: UserPw
			};
	
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
			
		}
		
		return false;
	};
	
    this.HardwareKeyAdminLogin = function(index, AdminPw) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeyAdminLogin",
				Index: index,
				AdminPw: AdminPw
			};
	
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
			
		}
		
		return false;
	};
	
    this.HardwareKeySetSoftIDString = function(index, SoftIDString) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeySetSoftIDString",
				Index: index,
				SoftIDString: SoftIDString
			};
	
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
			
		}
		
		return false;
	};
	
    this.HardwareKeyGetSoftIDString = function(index) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeyGetSoftIDString",
				Index: index
			};
	
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
			
		}
		
		return false;
	};
	
    this.HardwareKeyReadData = function(index, Address, Length) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeyReadData",
				Index: index,
				Address: Address,
				Length: Length
			};
	
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
			
		}
		return false;
	};
	
    this.HardwareKeyWriteData = function(index, Address, Length, Data) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeyWriteData",
				Index: index,
				Address: Address,
				Length: Length,
				Data: Data
			};
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
			
		}
		return false;
	};
	
    this.HardwareKey3DesSetKey = function(index, Key) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKey3DesSetKey",
				Index: index,
				Key: Key
			};
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
		}
		return false;
	};
	
    this.HardwareKey3DesEncrypt = function(index, Length, Text) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKey3DesEncrypt",
				Index: index,
				Length: Length,
				Text: Text
			};
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
		}
		return false;
	};
	
    this.HardwareKey3DesDecrypt = function(index, Length, Text) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKey3DesDecrypt",
				Index: index,
				Length: Length,
				Text: Text
			};
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
		}
		return false;
	};
	
    this.HardwareKeyDesSetKey = function(index, Key) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeyDesSetKey",
				Index: index,
				Key: Key
			};
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
		}
		return false;
	};
	
	
    this.HardwareKeyDesEncrypt = function(index, Length, Text) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeyDesEncrypt",
				Index: index,
				Length: Length,
				Text: Text
			};
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
		}
		return false;
	};
	
    this.HardwareKeyDesDecrypt = function(index, Length, Text) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeyDesDecrypt",
				Index: index,
				Length: Length,
				Text: Text
			};
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
		}
		return false;
	};
    this.HardwareKeySetAutoRunUrl = function(index, Url) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeySetAutoRunUrl",
				Index: index,
				Url: Url
			};
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
		}
		return false;
	};
	
    this.HardwareKeyMD5 = function(index, Length, Text) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeyMD5",
				Index: index,
				Length: Length,
				Text: Text
			};
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
		}
		return false;
	};
	
    this.HardwareKeySetMD5Key = function(index, Key) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeySetMD5Key",
				Index: index,
				Key: Key
			};
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
		}
		return false;
	};
	
    this.HardwareKeyHmacMD5 = function(index, Length, Text) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeyHmacMD5",
				Index: index,
				Length: Length,
				Text: Text
			};
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
		}
		return false;
	};
    this.HardwareKeySHA1 = function(index, Length, Text) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeySHA1",
				Index: index,
				Length: Length,
				Text: Text
			};
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
		}
		return false;
	};
    this.HardwareKeyHmacSHA1 = function(index, Length, Text) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeyHmacSHA1",
				Index: index,
				Length: Length,
				Text: Text
			};
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
		}
		return false;
	};
    this.HardwareKeySetSHA1Key = function(index, Key) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeySetSHA1Key",
				Index: index,
				Key: Key
			};
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
		}
		return false;
	};
    this.HardwareKeyGetCurrentPcChkData = function(index) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeyGetCurrentPcChkData",
				Index: index
			};
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
		}
		return false;
	};
    this.HardwareKeySetPcChkData = function(index, ChkData) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeySetPcChkData",
				Index: index,
				ChkData: ChkData
			};
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
		}
		return false;
	};
    this.HardwareKeyIsThisPc = function(index) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeyIsThisPc",
				Index: index
			};
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
		}
		return false;
	};
    this.HardwareKeyClearPcChkData = function(index) 
	{
		try
		{
			var msg = 
			{
				FunctionType: "HardwareKeyClearPcChkData",
				Index: index
			};
			this.HardwareKeySocket.send('255|HardwareKeyWebSocket|'+JSON.stringify(msg));
			return true;
		}	
		catch(exception)
		{
		}
		return false;
	};
}