import config
import config_modules
from whiteboard import whiteboard
from ca_logging import log
import logging
import argparse
from termcolor import colored, cprint
import datetime
import time
import traceback
import random

class TestCora():
    def __init__(self, timeit, autotest_script=None):
        self.name = "TestCora"
        self.autotest_script = autotest_script
        self.autotest_script_index = 0
        self.timeit = timeit

        self.client_id = "test" + datetime.datetime.now().__str__()
        self.create_services()
        self.use_local_DB_bool = False

    def set_use_local_DB_value(self, val):
        self.use_local_DB_bool = val
        for service in self.services:
            if "DM" in service.name:
                service.set_use_local_recipe_DB(val)

    def start_testCora(self):
        bool_continue = True
        if not self.autotest_script:
            print(colored("####################################################################################################","yellow"))
            print(colored("You are about to test the full Cora-system (server side).\n","yellow"))
            print(colored("Because you're testing the server side, this test is LOCAL and nothing transits through firebase.","yellow"))
            print(colored("Note that the data corresponding to this test is still be saved locally by the DataCollector module.\n","yellow"))
            if self.use_local_DB_bool:
                utterance = input(colored("/!\\/!\\/!\\ We'll be using the local recipe DB --> queries to the local DB are NOT personalized with the user's preferences.\nAre you OK with that? (y: yes, q: no, cancel and quit): ", "yellow"))
                if utterance == "q":
                    self.quit()
                    bool_continue = False
                else:
                    print(colored("Nice!","yellow"))
            if bool_continue:
                print(colored("Enjoy your interaction with Cora!","yellow"))
                print(colored("####################################################################################################","yellow"))
        if not self.autotest_script or bool_continue:
            self.subscribe_whiteboard(config.MSG_NLG + self.client_id)
            self.subscribe_whiteboard(config.MSG_DATACOL_OUT + self.client_id)
            self.timer_response_time = None
            self.next_input()

    def create_services(self):
        self.services = list()
        for module_config in config_modules.modules.modules:
            args = list(module_config.values())[2:]
            args.append(self.timeit)
            # print(*args)
            new_module = module_config["module"](self.client_id, *args)
            self.services.append(new_module)

        # star services in dedicated threads
        for s in self.services:
            s.start_service()


    def publish_whiteboard(self, message, topic):
        whiteboard.publish(message, topic)

    def on_whiteboard_message(self, message, topic):
        if config.MSG_NLG in topic:
            # self.publish_for_client(message, self.client_id, firebase_key=config.FIREBASE_KEY_DIALOG)
            print("Response time: %.3f sec" % (time.time() - self.timer_response_time))
            # if message['send_several_messages']:
            for sentence_delay_dict in message["sentences_and_delays"]:
                sentence, delay = sentence_delay_dict['sentence'], sentence_delay_dict['delay']
                # print(sentence, delay)
                if delay:
                    print("delay: %.2f" % delay)
                    time.sleep(delay)
                print(colored("Cora says: "+sentence, "red"))
                self.publish_whiteboard({"dialog": sentence}, config.MSG_DATACOL_IN + self.client_id)
            # print(colored("Cora says: "+message["sentence"], "red"))
            # self.publish_whiteboard({"dialog": message["sentence"]}, config.MSG_DATACOL_IN + self.client_id)
            if message["intent"] == "bye":
                self.quit()
            else:
                self.next_input()
        else:
            log.critical("Not implemented yet")

    def subscribe_whiteboard(self, topic):
        log.debug("%s subscribing to %s" %(self.name, topic))
        whiteboard.subscribe(subscriber=self, topic=topic)


    def next_input(self):
        if self.autotest_script:
            utterance = self.autotest_script[self.autotest_script_index]
            self.autotest_script_index += 1
            self.publish_whiteboard({"dialog": utterance}, config.MSG_DATACOL_IN + self.client_id)
            print(colored("User: "+utterance, "yellow"))
        else:
            utterance = input(colored("Enter text (q to quit): ","yellow"))
            if utterance == 'q':
                self.quit()
        topic = config.MSG_SERVER_IN + self.client_id
        self.timer_response_time = time.time()
        whiteboard.publish(utterance, topic)

    def quit(self):
        for c in self.services:
            c.stop_service()
        # exit(0)




if __name__ == "__main__":

    argp = argparse.ArgumentParser()
    argp.add_argument('domain', metavar='domain', type=str, help='Domain to test (e.g. movies? food?)')
    argp.add_argument("--autotest", help="To test the system with a predefined script (to write bellow directly in the python file)", action="store_true")
    argp.add_argument("--randomtest", help="To test the system with random utterances (chosen from list written in this file)", action="store_true")
    argp.add_argument("--test", help="To test the NLU module yourself", action="store_true")
    argp.add_argument("--logs", help="If you want to see the python logs in the console", action="store_true")
    argp.add_argument("--timeit", help="If you want get the execution time for each module", action="store_true")

    hi = ["hi", "hello", "good morning", "hiya", "hallo"]
    i_am_emotion = ["i m tired", "good", "amazing", "i feel great", "OK", "fine", "i m good", "exhausted", "i had a good night and i feel great this morning!", "not good", "i feel bad", "i am in a bad mood", "i am sick", "I have a headache"]
    diet = ["Dairy free", "Gluten Free", "Low carbs", "Ketonic", "Vegetarian", "Vegan", "Pescetarian"]
    time_options = ["I have time", "I don t have time", "I am in a rush", "something quick", "I have plenty of time", "not in a rush"]
    accept_recipe = ["no", "something else", "not that", "seems good", "yes", "sure", "I don t like salmon", "i don t like salad", "i don t like chicken"]
    conversation_stages = [hi, i_am_emotion, diet, time_options, accept_recipe]


    autotest_scripts = dict()
    # autotest_scripts["error_pop_from_empty_list"] = ["hello", "Lucile", "better now", "soup", "it s healthy and light", "bot too much yet", "very", 'i m vegetarian', "20 min", "nop",
    #                                                  "why not", "sure", 'something else than soup?', 'yep', "yep" 'no', 'ok', "seems nice", "ya", "good", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "no thanks"]
    autotest_scripts['test1'] = ['hi', 'Lucile', "yup", 'what my husband cooks', 'because i take care of the baby so i don\'t cook', 'vegan', 'up to an hour', 'broccoli', 'I prefer Spicy Garlic Lime Chicken']


    args = argp.parse_args()
    timeit = args.timeit if args.timeit else False
    if not args.logs:
        log.setLevel(logging.CRITICAL)

    try:
        test = None
        if(args.domain in ["movies", "food"]):
            config_modules.modules.set_domain(args.domain)
            if args.autotest and autotest_scripts:
                for script_name, script in autotest_scripts.items():
                    print(colored(script_name, "blue"))
                    test = TestCora(timeit, script)
                    test.start_testCora()

            elif args.test:
                test = TestCora(timeit)
                test.start_testCora()

            elif args.randomtest:
                script = list()
                for elt in conversation_stages:
                    script.append(random.choice(elt))
                for i in range(10):
                    script.append(random.choice(conversation_stages[-1]))
                test = TestCora(timeit, script)
                test.start_testCora()

            else:
                args.print_help()
        else:
            argp.print_help()

    except:
        print("except")
        if test:
            test.quit()
        exceptiondata = traceback.format_exc().splitlines()
        print(exceptiondata[0])
        print("  [...]")
        for line in exceptiondata[-9:]:
            # for line in exceptiondata:
            print(line)


