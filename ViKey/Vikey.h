#ifndef VIKEY_API
#define VIKEY_API

// 定义基本数据类型
typedef unsigned long DWORD;
typedef unsigned char BYTE;
typedef unsigned short WORD;
typedef char CHAR;
typedef wchar_t WCHAR;
typedef void* PVOID;
typedef BYTE* PBYTE;
typedef WORD* PWORD;
typedef DWORD* PDWORD;

// 移除__stdcall调用约定以避免编译警告
#define VIKEYAPI 
#define __stdcall


enum VikeyType
{
	ViKeyAPP = 0,						//应用型加密狗
	ViKeySTD = 1,						//标准型加密狗
	ViKeyNET = 2,						//网络型加密狗
	ViKeyPRO = 3,						//专业型加密狗
	ViKeyWEB = 4,						//网页验证型加密狗
	ViKeyTIME = 5,						//时间型加密狗（内置硬件时钟）
	ViKeyMultiFunctional = 0x0A,		//多功能加密狗  支持多应用 支持网络认证
	ViKeyMultiFunctionalTime = 0x0B,	//多功能时间加密狗
	ViKeyInvalid	//无效类型
};


#define ViKeyNoLevel		0	//无权限(未使用登录接口加密狗时此时权限为无权限)
#define ViKeyUserLevel		1	//用户权限(调用VikeyUserLogin登录加密狗成功后,此时权限为用户权限)
#define ViKeyAdminLevel		2	//管理员权限(调用VikeyAdminLogin登录加密狗成功后,此时权限为管理员权限)

#define VIKEY_SUCCESS				0x00000000 //成功
#define VIKEY_ERROR_NO_VIKEY			0x80000001 //未找到ViKey设备
#define VIKEY_ERROR_INVALID_PASSWORD		0x80000002 //密码错误
#define VIKEY_ERROR_NEED_FIND			0x80000003 //首先需要查找设备
#define VIKEY_ERROR_INVALID_INDEX		0x80000004 //无效索引
#define VIKEY_ERROR_INVALID_VALUE		0x80000005 //数值无效
#define VIKEY_ERROR_INVALID_KEY			0x80000006 //密钥无效
#define VIKEY_ERROR_GET_VALUE			0x80000007 //获取信息失败
#define VIKEY_ERROR_SET_VALUE			0x80000008 //设置信息失败
#define VIKEY_ERROR_NO_CHANCE			0x80000009 //没有机会
#define VIKEY_ERROR_NO_TAUTHORITY		0x8000000A //权限不足
#define VIKEY_ERROR_INVALID_ADDR_OR_SIZE	0x8000000B //地址或大小无效
#define VIKEY_ERROR_RANDOM				0x8000000C //获取随机数失败
#define VIKEY_ERROR_SEED				0x8000000D //获取种子失败
#define VIKEY_ERROR_CONNECTION			0x8000000E //连接错误
#define VIKEY_ERROR_CALCULATE			0x8000000F //算法计算错误
#define VIKEY_ERROR_MODULE				0x80000010 //模块错误
#define VIKEY_ERROR_GENERATE_NEW_PASSWORD	0x80000011 //生成新密码失败
#define VIKEY_ERROR_ENCRYPT_FAILED		0x80000012 //加密数据失败
#define VIKEY_ERROR_DECRYPT_FAILED		0x80000013 //解密数据失败
#define VIKEY_ERROR_ALREADY_LOCKED		0x80000014 //ViKey设备已经被锁定
#define VIKEY_ERROR_UNKNOWN_COMMAND		0x80000015 //无效命令
#define VIKEY_ERROR_NO_SUPPORT			0x80000016 //当前ViKey设备不支持此功能
#define VIKEY_ERROR_CATCH				0x80000017 //捕获异常
#define VIKEY_ERROR_GET_USBDATA			0x80000018 //获取USB数据失败
#define VIKEY_ERROR_SET_USBDATA			0x80000019 //设置USB数据失败
#define VIKEY_ERROR_TIME_MODULE			0x8000001A //硬件时间模块错误
#define VIKEY_ERROR_TIME_OUTAGE			0x8000001B //硬件时间电池电量不足，时间可能不准确，校准时间
#define VIKEY_ERROR_MAX_CONNECTION		0x8000001C //加密狗达到最大连接数
#define VIKEY_ERROR_COMMUNICATION		0x8000001D //加密狗通信数据错误
#define VIKEY_ERROR_TIME				0x8000001E //加密狗时间错误
#define VIKEY_ERROR_UNKNOWN_ERROR		0xFFFFFFFF //未知错误

//LED灯状态定义
#define LED_OFF			   0 //关闭
#define LED_ON			   1 //开启
#define LED_BLINK		   2 //闪烁
#define LED_OFF_BLINK	   3 //平时关闭-通讯时闪烁
#define LED_ON_BLINK	   4 //平时开启-通讯时闪烁


#ifdef __cplusplus
extern "C"{
#endif

//��˵����Ϊ���ó���Ա�����º���һĿ��Ȼ������ֻ�г�������ԭ�ͣ����ں������ܺͲ����Ľ����ڰ����ֲ����г���
//��˵�����뵽��������1-[�ĵ�����Ƶ�̳�]��Ŀ¼�²鿴��ViKeyϵ�м��ܹ�ʹ��˵���ֲᡷ�ĵ���

/*********For ViKeyAPP��ViKeySTD��ViKeyNet��ViKeyPRO��ViKeyTime APIs**********/
/*****************************************************************************/
/*                                      API                                  */
/*****************************************************************************/

/** 
 * @˵��   ���Ҽ�������ʹ������APIǰ�����ȵ��ôκ�����
 * @param  pdwCount [out]     ������ҵ�ϵͳ�д��ڼ��ܹ������ز��ҵ����ܹ��ĸ���
 * @return 0     ��ʾϵͳ�д���ViKey���ܹ���
 */
DWORD __stdcall VikeyFind(DWORD* pdwCount);

/** 
 * @˵��   ���Ҽ�����Ex��ʹ������APIǰ�����ȵ��ôκ�����
 * @param  pdwCount [out]     ������ҵ�ϵͳ�д��ڼ��ܹ�,���ز��ҵ����ܹ��ĸ������ų�������ܹ���
 * @return 0     ��ʾϵͳ�д���ViKey���ܹ���
 */
DWORD __stdcall VikeyFindEx(DWORD* pdwCount);

/** 
 * @˵��   �������档������ʹ�ü��ܹ���ص�APIʱ����Ҫ���ô˺������������档
 * @˵��	         �����ڳ����˳�ǰ�����ô˺�����
* @˵��	             ע�⣺������ô˺����������ʹ�ü��ܹ����API����Ҫ�ٴε���VikeyFind
 * @return 0     ��ʾ�����ɹ���
 */
DWORD __stdcall VikeyUninitialization();

/** 
 * @˵��   ��ȡ���ܹ���Ӳ��ID,���ܹ���Ӳ��ID�Ǽ��ܹ���Ψһ��ʶ��ÿ�����ܹ���Ӳ��ID����һ����
 * @param  Index    [in]     ָ��Ҫ�������ܹ������
 * @param  pdwHID   [out]    ���ؼ��ܹ���Ӳ��ID
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyGetHID(WORD Index, DWORD *pdwHID);

/** 
 * @˵��   ��ȡ���ܹ���Ӳ���ͺš�
 * @param  Index    [in]     ָ��Ҫ�������ܹ������
 * @param  pdwHID   [out]    ���ؼ��ܹ���Ӳ���ͺš�
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyGetType(WORD Index, VikeyType *pType);

/** 
 * @˵��   ��ȡ���ܹ��ĵ�ǰȨ��
 * @param  Index    [in]     ָ��Ҫ�������ܹ������
 * @param  pLevel   [out]    ���ؼ��ܹ��ĵ�ǰȨ�� 0��ʾ���ܹ���δ��¼  1��ʾ���ܹ����û�Ȩ��  2��ʾ���ܹ��ǹ���ԱȨ��
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyGetLevel(WORD Index, BYTE *pLevel);


/** 
 * @˵��   ���û����ܹ��Ĳ�Ʒ����
 * @param  Index    [in]     ָ��Ҫ�������ܹ������
 * @param  szName   [in]    16���ֽڵĲ�Ʒ����
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeySetPtroductName(WORD Index, WCHAR szName[16]);

/** 
 * @˵��   ��ȡ�����ܹ��Ĳ�Ʒ����
 * @param  Index    [in]     ָ��Ҫ�������ܹ������
 * @param  szName   [out]    16���ֽڵĲ�Ʒ����
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyGetPtroductName(WORD Index, WCHAR szName[16]);
DWORD __stdcall VikeyGetPtroductNameA(WORD Index, CHAR szName[16]);

//��½��ע�����ܹ�
//���ܹ����볤��8���ַ� ��ĸ������

/** 
 * @˵��   ���û�Ȩ�޵�¼���ܹ�
 * @param  Index    [in]     ָ��Ҫ�������ܹ������
 * @param  szName   [in]     8�ֽڵ��û�����
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyUserLogin(WORD Index, char * pUserPassWord);

/** 
 * @˵��   �Թ���ԱȨ�޵�¼���ܹ�
 * @param  Index    [in]     ָ��Ҫ�������ܹ������
 * @param  szName   [in]     8�ֽڵĹ���Ա����
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyAdminLogin(WORD Index, char * pAdminPassWord);

/** 
 * @˵��   ע����¼���ܹ� ע����ļ��ܹ�Ȩ��Ϊ0 
 * @param  Index    [in]     ָ��Ҫ�������ܹ������
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyLogoff(WORD Index);

//�������볢�Դ������޸�����

/** 
 * @˵��   �����û�Ȩ�������������Դ���
 * @param  Index      [in]     ָ��Ҫ�������ܹ������
 * @param  cAttempt   [in]     �û�Ȩ�������������Դ���  �������Ϊ0��ʾ������
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeySetUserPassWordAttempt(WORD Index, BYTE cAttempt);

/** 
 * @˵��   ���ù���ԱȨ�������������Դ���
 * @param  Index      [in]     ָ��Ҫ�������ܹ������
 * @param  cAttempt   [in]     ����ԱȨ�������������Դ���  �������Ϊ0��ʾ������
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeySetAdminPassWordAttempt(WORD Index, BYTE cAttempt);

/** 
 * @˵��   ��ȡ�û�Ȩ�����뵱ǰ���Դ������������Դ���
 * @param  Index              [in]      ָ��Ҫ�������ܹ������
 * @param  pcCurrentAttempt   [out]     �û�Ȩ�����뵱ǰ���Դ���  
 * @param  pcMaxAttempt       [out]     �û�Ȩ�������������Դ���  �������Ϊ0��ʾ������
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyGetUserPassWordAttempt(WORD Index, BYTE *pcCurrentAttempt, BYTE *pcMaxAttempt);


/** 
 * @˵��   ��ȡ����ԱȨ�����뵱ǰ���Դ������������Դ���
 * @param  Index              [in]      ָ��Ҫ�������ܹ������
 * @param  pcCurrentAttempt   [out]     ����ԱȨ�����뵱ǰ���Դ���  
 * @param  pcMaxAttempt       [out]     ����ԱȨ�������������Դ���  �������Ϊ0��ʾ������
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyGetAdminPassWordAttempt(WORD Index, BYTE *pcCurrentAttempt, BYTE *pcMaxAttempt);

/** 
 * @˵��   ���ü��ܹ����û�Ȩ������͹���ԱȨ������  ע����ô˺���ʱȷ���Ѿ�����ԱȨ�޵�¼  ��������ʧ��
 * @param  Index              [in]     ָ��Ҫ�������ܹ������
 * @param  pNewUserPassWord   [in]     8�ֽڵ��û�Ȩ������ 
 * @param  pNewAdminPassWord  [in]     8�ֽڵĹ���ԱȨ������
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyResetPassword(WORD Index, char * pNewUserPassWord, char * pNewAdminPassWord);

/** 
 * @˵��   ����LED�Ƶ�״̬    �̼��汾7.4����֧�ִ˹���
 * @param  Index              [in]     ָ��Ҫ�������ܹ������
 * @param  cLedState		  [in]     0 ->���� 1 ->���� 2 ->����
 * @return 0     ��ʾ�����ɹ�		   
 */									   
DWORD __stdcall VikeySetLED(WORD Index, BYTE cLedState);


//����ID��д
//����ID����8���ַ� ��ĸ������

/** 
 * @˵��   ���ü��ܹ���8���ֽ�����ID�ַ���
 * @param  Index              [in]     ָ��Ҫ�������ܹ������
 * @param  pSoftIDString      [in]     8���ֽ�����ID�ַ���
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeySetSoftIDString(WORD Index, char * pSoftIDString);

/** 
 * @˵��   ��ȡ���ܹ���8���ֽ�����ID�ַ���
 * @param  Index              [in]     ָ��Ҫ�������ܹ������
 * @param  pSoftIDString      [out]    8���ֽ�����ID�ַ���
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyGetSoftIDString(WORD Index, char * pSoftIDString);

//��д����
/** 
 * @˵��   ��ȡ���ܹ��е�����
 * @param  Index       [in]     ָ��Ҫ�������ܹ������
 * @param  Addr        [in]     ��ȡ�ĵ�ַ ��ʼλ��
 * @param  Length      [in]     ��ȡ�����ݳ���
 * @param  buffer      [out]    ���ض�ȡ����������
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyReadData(WORD Index, DWORD Addr, DWORD Length, BYTE * buffer);


/** 
 * @˵��   ����ܹ��е�д������
 * @param  Index       [in]     ָ��Ҫ�������ܹ������
 * @param  Addr        [in]     ��ȡ�ĵ�ַ ��ʼλ��
 * @param  Length      [in]     ��ȡ�����ݳ���
 * @param  buffer      [in]     д�����������
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyWriteData(WORD Index, DWORD Addr, DWORD Length, BYTE * buffer);

/** 
 * @˵��   �Ӽ��ܹ��еĻ�ȡ4��˫�ֵ����������
 * @param  Index          [in]      ָ��Ҫ�������ܹ������
 * @param  pwRandom1      [out]     �����1
 * @param  pwRandom2      [out]     �����2
 * @param  pwRandom3      [out]     �����3
 * @param  pwRandom4      [out]     �����4
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall ViKeyRandom(WORD Index, WORD* pwRandom1, WORD* pwRandom2, WORD* pwRandom3, WORD* pwRandom4);

//������ģ��
/** 
 * @˵��   ���ü��ܹ��еļ�����
 * @param  Index          [in]     ָ��Ҫ�������ܹ������
 * @param  wModuleIndex   [in]     ����������� ��0��ʼ
 * @param  wValue         [in]     �������еĳ�ʼֵ
 * @param  wMode          [in]     ��������ģʽ   1�������ݼ�  0���������ݼ�
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall ViKeySetModule(WORD Index, WORD wModuleIndex, WORD wValue, WORD wMode);

/** 
 * @˵��   ��ȡ���ܹ��еļ�����
 * @param  Index          [in]     ָ��Ҫ�������ܹ������
 * @param  wModuleIndex   [in]     ����������� ��0��ʼ
 * @param  pwValue        [out]    �������еĵ�ǰֵ
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall ViKeyGetModule(WORD Index, WORD wModuleIndex, WORD* pwValue);

/** 
 * @˵��   �Լ��ܹ��еļ��������еݼ�����
 * @param  Index          [in]     ָ��Ҫ�������ܹ������
 * @param  wModuleIndex   [in]     ����������� ��0��ʼ
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall ViKeyDecraseModule(WORD Index, WORD wModuleIndex);

/** 
 * @˵��   �Լ��ܹ��еļ��������м��
 * @param  Index          [in]     ָ��Ҫ�������ܹ������
 * @param  wModuleIndex   [in]     ����������� ��0��ʼ
 * @param  IsZero         [out]    ���ؼ������еĵ�ǰֵ�Ƿ�Ϊ0
 * @param  CanDecrase     [out]    ���ؼ������Ƿ������ݼ�
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall ViKeyCheckModule(WORD Index, WORD wModuleIndex, WORD *IsZero, WORD* CanDecrase);

//�ӽ���
enum Des3KeyLengthType
{
	Des3KeyLength16 = 0,
	Des3KeyLength24 = 1
};
/** 
 * @˵��   ���ü��ܹ���3DES�㷨�е���Կ
 * @param  Index          [in]     ָ��Ҫ�������ܹ������
 * @param  pKey           [in]     3DES�㷨�е���Կ
 * @param  KeyType        [in]     3DES�㷨�е���Կ����  0��ʾ��Կ����16�ֽ� 1��ʾ��Կ����24�ֽ�
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall Vikey3DesSetKey(WORD Index, BYTE * pKey, Des3KeyLengthType KeyType);

/** 
 * @˵��   ִ�м��ܹ���3DES�㷨�еļ��ܲ���
 * @param  Index          [in]     ָ��Ҫ�������ܹ������
 * @param  length         [in]     ���ݳ��� ���ĳ��ȱ���Ϊ8�ı���
 * @param  pText          [in]     Ҫ���ܵ���������
 * @param  pResult        [out]    ���ؼ������ݽ��
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall Vikey3DesEncrypt(WORD Index, WORD length, BYTE * pText, BYTE* pResult);

/** 
 * @˵��   ִ�м��ܹ���3DES�㷨�еĽ��ܲ���
 * @param  Index          [in]     ָ��Ҫ�������ܹ������
 * @param  length         [in]     ���ݳ��� ���ĳ��ȱ���Ϊ8�ı���
 * @param  pText          [in]     Ҫ���ܵ���������
 * @param  pResult        [out]    ���ؽ������ݽ��
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall Vikey3DesDecrypt(WORD Index, WORD length, BYTE * pText, BYTE* pResult);

/** 
 * @˵��   ���ü��ܹ���DES�㷨�е���Կ
 * @param  Index          [in]     ָ��Ҫ�������ܹ������
 * @param  pKey           [in]     DES�㷨�е���Կ ��Կ���ȹ̶�Ϊ8���ֽ�
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyDesSetKey(WORD Index, BYTE * pKey);

/** 
 * @˵��   ִ�м��ܹ���DES�㷨�еļ��ܲ���
 * @param  Index          [in]     ָ��Ҫ�������ܹ������
 * @param  length         [in]     ���ݳ��� ���ĳ��ȱ���Ϊ8�ı���
 * @param  pText          [in]     Ҫ���ܵ���������
 * @param  pResult        [out]    ���ؼ������ݽ��
 * @param  OutLength      [out]    ���ؼ������ݳ���
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyDesEncrypt(WORD Index, WORD InLength, BYTE * pText, BYTE* pResult, WORD *OutLength);

/** 
 * @˵��   ִ�м��ܹ���DES�㷨�еĽ��ܲ���
 * @param  Index          [in]     ָ��Ҫ�������ܹ������
 * @param  length         [in]     ���ݳ��� �����ĳ��ȱ���Ϊ8�ı���
 * @param  pText          [in]     Ҫ���ܵ���������
 * @param  pResult        [out]    ���ؽ������ݽ��
 * @param  OutLength      [out]    ���ؽ������ݳ���
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyDesDecrypt(WORD Index, WORD InLength, BYTE * pText, BYTE* pResult, WORD *OutLength);

//�Զ�����ҳ�ӿ�
/** 
 * @˵��   ���ü��ܹ����Զ�����ַ
 * @param  Index          [in]     ָ��Ҫ�������ܹ������
 * @param  pUrl           [in]     ��ַ
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeySetAutoRunUrl(WORD Index, BYTE *pUrl);

/** 
 * @˵��   ��ȡ���ܹ����Զ�����ַ
 * @param  Index          [in]     ָ��Ҫ�������ܹ������
 * @param  pUrl           [out]    ��ַ
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyGetAutoRunUrl(WORD Index, BYTE *pUrl);

//For ViKeyNET��ViKeyPRO
/** 
 * @˵��   ����������ܹ���������ӵĿͻ�������
 * @param  Index          [in]     ָ��Ҫ�������ܹ������
 * @param  dwCount        [in]     ������ӵĿͻ�������
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeySetMaxClientCount(WORD Index, WORD dwCount);

/** 
 * @˵��   ��ȡ������ܹ���������ӵĿͻ�������
 * @param  Index          [in]     ָ��Ҫ�������ܹ������
 * @param  pdwCount       [out]    ����������ӵĿͻ�������
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyGetMaxClientCount(WORD Index, WORD* pdwCount);

//For ViKeyWEB��ViKeyPRO
/** 
 * @˵��   ִ�м��ܹ���MD5�㷨
 * @param  Index         [in]     ָ��Ҫ�������ܹ������
 * @param  length        [in]     ���ݳ���
 * @param  pText         [in]     ��������
 * @param  pResult       [out]    ����MD5�㷨���  16�ֽ�
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyMD5(WORD Index, WORD length, BYTE * pText, BYTE* pResult);

/** 
 * @˵��   ���ü��ܹ���HMAC-MD5�㷨����Կ
 * @param  Index         [in]     ָ��Ҫ�������ܹ������
 * @param  pMD5key       [in]     ��Կ���� ��0��β
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeySetMD5Key(WORD Index, BYTE * pMD5key);

/** 
 * @˵��   ִ�м��ܹ���HMAC-MD5�㷨
 * @param  Index         [in]     ָ��Ҫ�������ܹ������
 * @param  length        [in]     ���ݳ���
 * @param  pText         [in]     ��������
 * @param  pResult       [out]    ����HMAC-MD5�㷨�ļ��ܽ��
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyHmacMD5(WORD Index, WORD length, BYTE * pText, BYTE* pResult);

/** 
 * @˵��   ִ�м��ܹ���SHA1�㷨
 * @param  Index         [in]     ָ��Ҫ�������ܹ������
 * @param  length        [in]     ���ݳ���
 * @param  pText         [in]     ��������
 * @param  pResult       [out]    ����SHA1�㷨���  20�ֽ�
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeySHA1(WORD Index, WORD length, BYTE * pText, BYTE* pResult);

/** 
 * @˵��   ���ü��ܹ���HMAC-SHA1�㷨����Կ
 * @param  Index         [in]     ָ��Ҫ�������ܹ������
 * @param  pSHA1key      [in]     ��Կ���� ��0��β
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeySetSHA1Key(WORD Index, BYTE * pSHA1key);

/** 
 * @˵��   ִ�м��ܹ���HMAC-SHA1�㷨
 * @param  Index         [in]     ָ��Ҫ�������ܹ������
 * @param  length        [in]     ���ݳ���
 * @param  pText         [in]     ��������
 * @param  pResult       [out]    ����HMAC-SHA1�㷨�ļ��ܽ��
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyHmacSHA1(WORD Index, WORD length, BYTE * pText, BYTE* pResult);

/** 
 * @˵��   ִ�м��ܹ�����SM3�㷨
 * @param  Index         [in]     ָ��Ҫ�������ܹ������
 * @param  length        [in]     �������ݵĳ���
 * @param  pText         [in]     �������ݵ�����
 * @param  pResult       [out]    ����SM3�㷨���  ����Ϊ32�ֽ�
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeySM3(WORD Index, WORD length, BYTE * pText, BYTE* pResult);


/** 
 * @˵��   ���ü��ܹ���SM4�㷨�е���Կ
 * @param  Index          [in]     ָ��Ҫ�������ܹ������
 * @param  pKey           [in]     SM4�㷨�е���Կ ��Կ���ȹ̶�Ϊ16���ֽ�
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeySM4SetKey(WORD Index, BYTE * pKey);

/** 
 * @˵��   ִ�м��ܹ���SM4�㷨�еļ��ܲ���
 * @param  Index          [in]     ָ��Ҫ�������ܹ������
 * @param  length         [in]     ���ݳ��� ���ȱ���Ϊ16�ı���
 * @param  pText          [in]     Ҫ���ܵ���������

 * @param  pResult        [out]    ���ؼ������ݽ��
 * @param  OutLength      [out]    ���ؼ������ݳ���
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeySM4Encrypt(WORD Index, WORD InLength, BYTE * pText, BYTE* pResult, WORD *OutLength);

/** 
 * @˵��   ִ�м��ܹ���SM4�㷨�еĽ��ܲ���
 * @param  Index          [in]     ָ��Ҫ�������ܹ������
 * @param  length         [in]     �������ݳ��� ���ȱ���Ϊ16�ı���
 * @param  pText          [in]     Ҫ���ܵ�������������

 * @param  pResult        [out]    ���ؽ������ݽ��
 * @param  OutLength      [out]    ���ؽ������ݳ���
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeySM4Decrypt(WORD Index, WORD InLength, BYTE * pText, BYTE* pResult, WORD *OutLength);

/** 
 * @˵��   ִ�зǶԳƼ���SM2�㷨����Կ��
 * @param  Index          [in]     ָ��Ҫ�������ܹ������

 * @param  pPrivateKey    [out]    ����˽Կ
 * @param  pPublicKey     [out]    ���ع�Կ
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeySM2CreateKey(WORD Index, BYTE * pPrivateKey, BYTE* pPublicKey);


/** 
 * @˵��   SM2�㷨ͨ��˽Կ���㹫Կ
 * @param  Index          [in]     ָ��Ҫ�������ܹ������
 * @param  pPrivateKey    [in]     ����˽Կ ����Ϊ32�ֽ�

 * @param  pPublicKey     [out]    ���ع�Կ
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeySM2CalcPubKey(WORD Index, BYTE * pPrivateKey, BYTE* pPublicKey);

/** 
 * @˵��   SM2�㷨ͨ��˽Կǩ������
 * @param  Index			[in]     ָ��Ҫ�������ܹ������
 * @param  pPrivateKey		[in]     ����˽Կ
 * @param  pUserID			[in]     �����û�ID
 * @param  wUserIDLength    [in]     �����û�ID����
 * @param  pData			[in]     ����Ҫǩ��������
 * @param  wDataLength		[in]     ����Ҫǩ�������ݳ���

 * @param  pSignR			[out]    ����ǩ��R
 * @param  pSignS			[out]    ����ǩ��S
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeySM2Sign(WORD Index, BYTE * pPrivateKey, BYTE* pUserID, WORD wUserIDLength, BYTE* pData, WORD wDataLength, BYTE* pSignR, BYTE* pSignS);

/** 
 * @˵��   SM2�㷨ͨ����Կ��֤ǩ��
 * @param  Index			[in]     ָ��Ҫ�������ܹ������
 * @param  pPublicKey		[in]     ���빫Կ
 * @param  pUserID			[in]     �����û�ID
 * @param  wUserIDLength    [in]     �����û�ID����
 * @param  pData			[in]     ����Ҫ��ǩ������
 * @param  wDataLength		[in]     ����Ҫ��ǩ�����ݳ���
 * @param  pSignR			[in]     ����ǩ��R
 * @param  pSignS			[in]     ����ǩ��S

 * @return 0     ��ʾ������֤ǩ���ɹ�
 */
DWORD __stdcall VikeySM2Verify(WORD Index, BYTE * pPublicKey, BYTE* pUserID, WORD wUserIDLength, BYTE* pData, WORD wDataLength, BYTE* pSignR, BYTE* pSignS);

/** 
 * @˵��   SM2�㷨ͨ����Կ�������ݼ���
 * @param  Index			[in]     ָ��Ҫ�������ܹ������
 * @param  pPublicKey		[in]     ���빫Կ
 * @param  pData			[in]     ������ܵ�����
 * @param  wDataLength		[in]     ������ܵ����ݳ���

 * @param  pResult			[out]    ������ܺ�Ľ������
 * @param  wResultLength	[out]    ������ܺ�Ľ�����ĳ���

 * @return 0     ��ʾ�������ܳɹ�
 */
DWORD __stdcall VikeySM2Encrypt(WORD Index, BYTE * pPublicKey, BYTE* pData, WORD wDataLength, BYTE* pResult, WORD *wResultLength);

/** 
 * @˵��   SM2�㷨ͨ��˽Կ�������ݽ���
 * @param  Index			[in]     ָ��Ҫ�������ܹ������
 * @param  pPrivateKey		[in]     ����˽Կ
 * @param  pData			[in]     ������ܵ�����
 * @param  wDataLength		[in]     ������ܵ����ݳ���

 * @param  pResult			[out]    ������ܺ�Ľ������
 * @param  wResultLength	[out]    ������ܺ�Ľ�����ĳ���

 * @return 0     ��ʾ�������ܳɹ�
 */
DWORD __stdcall VikeySM2Decrypt(WORD Index, BYTE * pPrivateKey, BYTE* pData, WORD wDataLength, BYTE* pResult, WORD *wResultLength);
//For ViKeyTIME
typedef struct _VIKEY_TIME 
{ 
	BYTE cYear;	      //��	
	BYTE cMonth;      //��
	BYTE cDay;        //��
	BYTE cHour;       //ʱ
	BYTE cMinute;     //��
	BYTE cSecond;     //��

	bool operator < (const _VIKEY_TIME &another) const;
	bool operator > (const _VIKEY_TIME &another) const;
} SVikeyTime, *PVIKEYTIME;

/** 
 * @˵��   ��ȡʱ���ͼ��ܹ��е��ڲ�����ʱ��
 * @param  Index         [in]     ָ��Ҫ�������ܹ������
 * @param  pTime         [out]    ����ʱ���ͼ��ܹ��еĵ�ǰʱ�� 6���ֽ� XX��XX��XX��XXʱXX��XX��
 * @return 0     ��ʾ�����ɹ�
 */

DWORD __stdcall VikeyGetTime(WORD Index, PVIKEYTIME pTime);

/** 
 * @˵��   ��ȡʱ���ͼ��ܹ��еĵ���ʱ��
 * @param  Index         [in]     ָ��Ҫ�������ܹ������
 * @param  pTime         [out]    ����ʱ���ͼ��ܹ��еĵ���ʱ�� 6���ֽ� XX��XX��XX��XXʱXX��XX��
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyGetValidTime(WORD Index, PVIKEYTIME pTime);

/** 
 * @˵��   ����ʱ���ͼ��ܹ��еĵ���ʱ��
 * @param  Index         [in]     ָ��Ҫ�������ܹ������
 * @param  pTime         [in]    ����ʱ���ͼ��ܹ��еĵ���ʱ�� 6���ֽ� XX��XX��XX��XXʱXX��XX��
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeySetValidTime(WORD Index, PVIKEYTIME pTime);

/** 
 * @˵��   ���ʱ���ͼ��ܹ���ʱ�ӹ����Ƿ���
 * @param  Index         [in]     ָ��Ҫ�������ܹ������
 * @param  pTime         [out]    �����Ƿ��ڽ�� 1��ʾû�е���   0��ʾ�Ѿ�����
 * @return 0     ��ʾ�����ɹ�
 */
DWORD __stdcall VikeyCheckValidTime(WORD Index, BYTE * pIsValid);

#ifdef __cplusplus
} //  extern "C"{
#endif

#endif
