import logging

from okcupyd.db import model, txn


log = logging.getLogger(__name__)


class UserAdapter(object):

    def __init__(self, profile):
        self.profile = profile

    def build(self):
        return model.User(okc_id=self.profile.id,
                          handle=self.profile.username,
                          age=self.profile.age,
                          location=self.profile.location)

    def get(self):
        return model.User.upsert_okc(self.build(), id_key='okc_id')

    def get_no_txn(self, session):
        return model.User.upsert_one_no_txn(session, self.build(),
                                            id_key='okc_id')


class ThreadAdapter(object):

    def __init__(self, thread):
        self.thread = thread

    def _get_thread(self, session):
        initiator = UserAdapter(self.thread.initiator).get_no_txn(session)
        respondent = UserAdapter(self.thread.respondent).get_no_txn(session)
        message_thread = model.MessageThread(okc_id=self.thread.id,
                                             initiator=initiator,
                                             respondent=respondent)
        return model.MessageThread.upsert_one_no_txn(session, message_thread,
                                                     id_key='okc_id')

    def _add_messages(self, thread_model):
        existing_message_ids = set([m.okc_id for m in thread_model.messages])
        new_messages = [message for message in self.thread.messages
                        if message.id not in existing_message_ids]
        for new_message in new_messages:
            from_initiator = thread_model.initiator.handle.lower() == \
                             new_message.sender.lower()
            sender, recipient = (thread_model.initiator,
                                 thread_model.respondent) \
                                if from_initiator else \
                                (thread_model.respondent,
                                 thread_model.initiator)
            thread_model.messages.append(
                model.Message(okc_id=new_message.id,
                              text=new_message.content,
                              sender=sender,
                              recipient=recipient)
            )
        return thread_model

    def add_messages(self):
        with txn() as session:
            thread_model = model.MessageThread.find_no_txn(session,
                                                           self.thread.id,
                                                           id_key='okc_id')
            return self._add_messages(thread_model)

    def get_thread(self):
        with txn() as session:
            thread_model = self._get_thread(session)
            return self._add_messages(thread_model)
