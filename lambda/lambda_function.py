"""
 Copyright (C) 2020 Dabble Lab - All Rights Reserved
 You may use, distribute and modify this code under the
 terms and conditions defined in file 'LICENSE.txt', which
 is part of this source code package.
 
 For additional copyright information please
 visit : http://dabblelab.com/copyright
 """

from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.dispatch_components import (AbstractRequestHandler, AbstractExceptionHandler, AbstractRequestInterceptor, AbstractResponseInterceptor)
from ask_sdk_s3.adapter import S3Adapter
from ask_sdk_model.ui import SimpleCard
from ask_sdk_core.skill_builder import CustomSkillBuilder

import logging
import json
import random
import os

from dotenv import load_dotenv

s3_adapter = S3Adapter(bucket_name = os.environ.get("S3_PERSISTENCE_BUCKET"))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Handlers

# This handler responds when required environment variables are missing
class InvalidConfigHandler(AbstractRequestHandler):
    
    def can_handle(self, handler_input):
        request_attributes = handler_input.attributes_manager.request_attributes
        invalid_config = request_attributes["invalid_config"]
        return invalid_config
        
    def handle(self,handler_input):
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        speech_output = language_prompts["ENV_NOT_CONFIGURED"]
        return ( 
            handler_input.response_builder
                .speak(speech_output)
                .response )

class InvalidConfigInterceptor(AbstractRequestInterceptor):
    def process(self, handler_input):
        try:
            load_dotenv()
            handler_input.attributes_manager.request_attributes["invalid_config"] = False
        except:
            handler_input.attributes_manager.request_attributes["invalid_config"] = True

class LaunchRequestHandler(AbstractRequestHandler):
    
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)
    
    def handle(self, handler_input):
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        persistent_attributes = handler_input.attributes_manager.persistent_attributes
        session_attributes = handler_input.attributes_manager.session_attributes
        
        try:
            user_name = persistent_attributes["user_name"]
        except:
            user_name = None
        
        skill_name = language_prompts["SKILL_NAME"]
        
        if user_name is not None:
            speech_output = random.choice(language_prompts["GREETING"]).format(user_name)
            reprompt = random.choice(language_prompts["GREETING_REPROMPT"])
        else:
            speech_output = random.choice(language_prompts["GREETING_UNKNOWN_USER"]).format(skill_name)
            reprompt = random.choice(language_prompts["GREETING_UNKNOWN_USER_REPROMPT"])
        
        session_attributes["repeat_speech_output"] = speech_output
        session_attributes["repeat_reprompt_output"] = reprompt
        
        return (
            handler_input.response_builder
                .speak(speech_output)
                .ask(reprompt)
                .set_card(SimpleCard(skill_name,speech_output))
                .response
            )

class MyNameIsIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("MyNameIsIntent")(handler_input)
    
    def handle(self,handler_input):
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        user_name = handler_input.request_envelope.request.intent.slots["name"].value
        
        speech_output = random.choice(language_prompts["GREETING_RESPONSE"]).format(user_name)
        
        handler_input.attributes_manager.persistent_attributes["user_name"] = user_name
        handler_input.attributes_manager.save_persistent_attributes()
        
        return(
            handler_input.response_builder
                .speak(speech_output)
                .response
            )

class LearnMoreIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("LearnMoreIntent")(handler_input)
    
    def handle(self, handler_input):
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        
        speech_output = random.choice(language_prompts["LEARN_MORE"])
        return (
            handler_input.response_builder
                .speak(speech_output)
                .response
            )

# This handler is used to handle the AMAZON.RepeatIntent. It lets users ask Alexa to repeat the last thing that was said.
class RepeatIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.RepeatIntent")(handler_input)
    
    def handle(self, handler_input):
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        session_attributes = handler_input.attributes_manager.session_attributes
        
        repeat_speech_output = session_attributes["repeat_speech_output"]
        repeat_reprompt_output = session_attributes["repeat_reprompt_output"]
        
        speech_output = random.choice(language_prompts["REPEAT"]).format(repeat_speech_output)
        reprompt = random.choice(language_prompts["REPEAT_REPROMPT"]).format(repeat_reprompt_output)
        
        return (
            handler_input.response_builder
                .speak(speech_output)
                .ask(reprompt)
                .response
            )

class YesNoIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.YesIntent")(handler_input) or
                is_intent_name("AMAZON.NoIntent")(handler_input))
    
    def handle(self, handler_input):
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        session_attributes = handler_input.attributes_manager.session_attributes
        
        speech_output = ""
        
        if is_intent_name("AMAZON.YesIntent")(handler_input):
            return LearnMoreIntentHandler.handle(handler_input)
        else:
            speech_output = random.choice(language_prompts["NO"])
        
        return (
            handler_input.response_builder
                .speak(speech_output)
                .response
            )



class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))
    
    def handle(self, handler_input):
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        speech_output = random.choice(language_prompts["CANCEL_STOP_RESPONSE"])
        
        return (
            handler_input.response_builder
                .speak(speech_output)
                .set_should_end_session(True)
                .response
            )

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)
    
    def handle(self, handler_input):
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        speech_output = random.choice(language_prompts["HELP"])
        reprompt = random.choice(language_prompts["HELP_REPROMPT"])
        
        return (
            handler_input.response_builder
                .speak(speech_output)
                .ask(reprompt)
                .response
            )

# This function handles utterances that can't be matched to any other intent handler.
class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)
    
    def handle(self, handler_input):
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        speech_output = random.choice(language_prompts["FALLBACK"])
        reprompt = random.choice(language_prompts["FALLBACK_REPROMPT"])
        
        return (
            handler_input.response_builder
                .speak(speech_output)
                .ask(reprompt)
                .response
            )


class SessionEndedRequesthandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)
    
    def handle(self, handler_input):
        logger.info("Session ended with the reason: {}".format(handler_input.request_envelope.request.reason))
        return handler_input.response_builder.response


# This function handles syntax or routing errors. If you receive an error stating the request
# handler is not found, you have not implemented a handler for the intent or included
# it in the skill builder below
class CatchAllExceptionHandler(AbstractExceptionHandler):
    
    def can_handle(self, handler_input, exception):
        return True
    
    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)
        
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        
        speech_output = language_prompts["ERROR"]
        reprompt = language_prompts["ERROR_REPROMPT"]
        
        return (
            handler_input.response_builder
                .speak(speech_output)
                .ask(reprompt)
                .response
            )

class RequestLogger(AbstractRequestInterceptor):

    def process(self, handler_input):
        logger.debug("Alexa Request: {}".format(
            handler_input.request_envelope.request))

class ResponseLogger(AbstractResponseInterceptor):

    def process(self, handler_input, response):
        logger.debug("Alexa Response: {}".format(response))

# This interceptor function is used for supporting different languages and locales.
class LocalizationInterceptor(AbstractRequestInterceptor):

    def process(self, handler_input):
        locale = handler_input.request_envelope.request.locale
        logger.info("Locale is {}".format(locale))
        
        try:
            with open("languages/"+str(locale)+".json") as language_data:
                language_prompts = json.load(language_data)
        except:
            with open("languages/"+ str(locale[:2]) +".json") as language_data:
                language_prompts = json.load(language_data)
        
        handler_input.attributes_manager.request_attributes["_"] = language_prompts


sb = CustomSkillBuilder (persistence_adapter = s3_adapter)
sb.add_request_handler(InvalidConfigHandler())
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(MyNameIsIntentHandler())
sb.add_request_handler(LearnMoreIntentHandler())
sb.add_request_handler(YesNoIntentHandler())
sb.add_request_handler(RepeatIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequesthandler())

sb.add_exception_handler(CatchAllExceptionHandler())

sb.add_global_request_interceptor(LocalizationInterceptor())
sb.add_global_request_interceptor(InvalidConfigInterceptor())
sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())

lambda_handler = sb.lambda_handler()