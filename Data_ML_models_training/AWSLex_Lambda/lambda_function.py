### Required Libraries ###
from datetime import datetime
from dateutil.relativedelta import relativedelta
import recommendations
import kraken

def getBalance():
    result = kraken.getMyBalance()
    balance = ""
    for key, data in result.items():
        balance = balance + "[" + key + ":" + data + "], "
    return balance
    
### Function to decide the recommendation based on the risk level ###
def getRecommendation():
    
    # crypto = crypto.lower()
    
    # if crypto == "BTC":
    #     return "BTC"
    # elif crypto == "ETH":
    #     return "ETH"
    # elif crypto == "ADA":
    #     return "ADA"
    # elif crypto == "LTC":
    #     return "LTC"
    # elif crypto == 'Recommend':
    return recommendations.getPredictedSignals()

def getCoinAbbreviation(coin):
    coin = coin.lower()
    
    if coin == "btc" or coin == "bitcoin":
        return 'XBTAUD'
    elif coin == "eth" or coin == "ethereum":
        return 'ETHAUD'
    elif coin == "ada" or coin == "cardano":
        return 'ADAAUD'
    elif coin == "ltc" or coin == "litecoin":
        return 'LTCAUD'
    elif coin == "steller" or coin == "xlm":
        return 'XXLMZAUD'
    elif coin == "ripple" or coin == "xrp":
        return 'XRPAUD'
    elif coin == "bitcoin cash" or coin == "bch":
        return 'BCHAUD'
        
def minimumCoinVolume(coin):
    coin = coin.lower()
    
    if coin == "btc" or coin == "bitcoin":
        return parse_float(0.0001)
    elif coin == "eth" or coin == "ethereum":
        return parse_float(0.004)
    elif coin == "ada" or coin == "cardano":
        return parse_float(5)
    elif coin == "ltc" or coin == "litecoin":
        return parse_float(0.03)
    elif coin == "steller" or coin == "xlm":
        return parse_float(10)
    elif coin == "ripple" or coin == "xrp":
        return parse_float(5)
    elif coin == "bitcoin cash" or coin == "bch":
        return parse_float(0.01)

def calculateMaxCoinToBuy(coin):
    cash = kraken.getCashBalance()
    bid = kraken.getBidPrice(coin)
    max_coin = cash/bid
    return max_coin
    
def executeTrade(crypto, coins):
    coinpair = getCoinAbbreviation(crypto)
    coins = parse_float(coins)
    result = kraken.placeOrder("market","buy", coinpair, 0, coins)
    balance = getBalance()
    return balance
    
balance = getBalance()
recommendations = getRecommendation()

### Functionality Helper Functions ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return int(n)
    except ValueError:
        return float("nan")
        
### Functionality Helper Functions ###
def parse_float(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return float(n)
    except ValueError:
        return float("nan")

def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }

def validate_data(age, crypto,recommend, coins, intent_request):
    """
    Validates the data provided by the user.
    """

    # Validate the retirement age based on the user's current age.
    # An retirement age of 65 years is considered by default.
    if age is not None:
        age = parse_int(
            age
        )  # Since parameters are strings it's important to cast values
        if age < 0:
            return build_validation_result(
                False,
                "age",
                "Silly human you cannot be less then zero, try again",
            )
        elif age >= 65:
            return build_validation_result(
                False,
                "age",
                "You are too old, you must travel back in time for me to help you."
                "can you provide an age between 0 and 64 please?",
            )

    # # Validate the investment amount, it should be >= 5000
    # if investment_amount is not None:
    #     investment_amount = parse_int(investment_amount)
    #     if investment_amount < 5000:
    #         return build_validation_result(
    #             False,
    #             "investmentAmount",
    #             "The minimum investment amount is $5,000 USD, "
    #             "could you please provide a greater amount?",
    #         )
    
    #Get recommendations
    if recommend is not None and crypto is None :
        if recommend.lower() == 'yes':
            # results = getRecommendation()
            message = "As someone who has come from the Future, my recommendations are as follows:\n" + recommendations
            
            return build_validation_result(
                True,
                "crypto",
                message,
            )
        elif recommend.lower() == 'no':
            # results = getRecommendation()
            message = "Alas! I knew the future but you missed out. Please select the coin you want to buy."
        
            return build_validation_result(
                True,
                "crypto",
                message,
            )
    
    if recommend is not None and crypto is not None and coins is None:
        coinpair = getCoinAbbreviation(crypto)
        max_vol = calculateMaxCoinToBuy(coinpair)
        min_vol = minimumCoinVolume(crypto)
        message = "Your balance in the exchange is: " + balance + ". Based on available cash balance in your exchange, maximum " + crypto + " you can buy is " + str(max_vol) + ". Please enter the amount of coins to buy keeping in mind the maximum volume."
        
        if max_vol < min_vol:
            return build_validation_result(
                False,
                "crypto",
                "You dont have sufficient balance to buy minimum volume required (" + str(min_vol) + ") of " + crypto + ". Please choose another coin or top up your balance in the exchange.", 
            )
        
        return build_validation_result(
            True,
            "coins",
            message,
        )
        
    if recommend is not None and crypto is not None and coins is not None:
        coinpair = getCoinAbbreviation(crypto)
        max_vol = calculateMaxCoinToBuy(coinpair)
        min_vol = minimumCoinVolume(crypto)
        coins = parse_float(coins)
        if coins > max_vol:
            return build_validation_result(
                False,
                "coins",
                "The maximum coins you can buy with available balance is " + str(max_vol) + ", "
                "could you please provide a lesser or equivalent amount?",
            )
        elif coins <= 0 :
            return build_validation_result(
                False,
                "coins",
                "Number of coins cannot be 0 or less."
                "Can you provide a number between " + str(min_vol) + " and " + str(max_vol),
            )

    return build_validation_result(True, None, None)


### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """
    return intent_request["currentIntent"]["slots"]


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }
    
def elicit_intent(session_attributes, message):
    """
    Defines an elicit intent type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitIntent",
            "message": message,
        },
    }


def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }


def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """

    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }

    return response


### Intents Handlers ###
def recommend_crypto(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio.
    """

    first_name = get_slots(intent_request)["firstName"]
    age = get_slots(intent_request)["age"]
    recommend = get_slots(intent_request)["recommend"]
    crypto = get_slots(intent_request)["crypto"]
    coins = get_slots(intent_request)["coins"]
    source = intent_request["invocationSource"]

    if source == "DialogCodeHook":
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt
        # for the first violation detected.
        slots = get_slots(intent_request)

        validation_result = validate_data(age, crypto, recommend,coins, intent_request)
        if not validation_result["isValid"]:
            slots[validation_result["violatedSlot"]] = None  # Cleans invalid slot

            # Returns an elicitSlot dialog to request new data for the invalid slot
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            )
            
        if validation_result["isValid"] and "message" in validation_result:
           if validation_result["message"] is not None and validation_result["violatedSlot"] is not None:
                return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            )

        # Fetch current session attibutes
        output_session_attributes = intent_request["sessionAttributes"]

        return delegate(output_session_attributes, get_slots(intent_request))
        
     # Execute trade and get new balance
    balance = executeTrade(crypto, coins)

    # Return a message with the initial recommendation based on the risk level.
    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": """{} your trade has been executed. Your new balance is {}.
            """.format(
                first_name,
                balance
            ),
        },
    )


### Intents Dispatcher ###
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    intent_name = intent_request["currentIntent"]["name"]

    # Dispatch to bot's intent handlers
    if intent_name == "RecommendCrypto":
        return recommend_crypto(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")


### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """

    return dispatch(event)

