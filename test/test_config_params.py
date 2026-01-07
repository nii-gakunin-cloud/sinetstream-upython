import unittest
import random
import sinetstream


SERVICE = "raspipicow"

def gen_client_id():
    return f"clid-{random.randint(0, 999999)}"

def gen_topic():
    return f"topic-{random.randint(0, 999999)}"

def gen_msg():
    return f"msg-{random.randint(0, 999999)}"


class TestConfigParams(unittest.TestCase):
    def _test_pubsub(self, kwargsW, kwargsR, topic=None, bytearrayp=False, kwargsPub={}, extraSub=lambda _: None):

        msgs = [gen_msg() for _ in range(1,random.randint(1,10))]
        if bytearrayp:
            msgs = [s.encode() for s in msgs]

        if topic is None:
            topic = gen_topic()
        with sinetstream.MessageReader(SERVICE, topic, **kwargsR) as rd:
            with sinetstream.MessageWriter(SERVICE, topic, **kwargsW) as wr:
                for m1 in msgs:
                    wr.publish(m1, **kwargsPub)

                    it = iter(rd)
                    m2 = next(it)
                    assert m2.value == m1
                    extraSub(m2)

    def test_base(self):
        kwargs = dict()
        self._test_pubsub(kwargs, kwargs)

    ##################### test type
    @unittest.expectedFailure
    def test_type_kafka(self):
        kwargs = dict(
            type="kafka"  # kafka is not supported
        )
        self._test_pubsub(kwargs, kwargs)

    ##################### test brokers
    @unittest.expectedFailure
    def test_brokers_empty(self):
        kwargs = dict(
            brokers=""  # invalid address
        )
        self._test_pubsub(kwargs, kwargs)

    ##################### test topic
    @unittest.expectedFailure
    def test_topic_empty(self):
        kwargs = dict()
        self._test_pubsub(kwargs, kwargs, topic="")  # invalid topic

    ##################### test client_id
    #@unittest.expectedFailure
    #def test_client_id_empty(self):
    #    kwargs = dict(
    #        client_id="",
    #    )
    #    self._test_pubsub(kwargs, kwargs)

    @unittest.expectedFailure
    def test_client_id_True(self):
        kwargs = dict(
            client_id=True,  # invalid
        )
        self._test_pubsub(kwargs, kwargs)

    ##################### test consistency
    @unittest.expectedFailure
    def test_consistecy_None(self):
        kwargs = dict(
            consistency=None,
        )
        self._test_pubsub(kwargs, kwargs)

    def test_consistecy_atmostonce(self):
        kwargs = dict(
            consistency=sinetstream.AT_MOST_ONCE,
        )
        self._test_pubsub(kwargs, kwargs)

    def test_consistecy_atleastonce(self):
        kwargs = dict(
            consistency=sinetstream.AT_LEAST_ONCE,
        )
        self._test_pubsub(kwargs, kwargs)

    @unittest.expectedFailure
    def test_consistecy_exactlyonce(self):
        kwargs = dict(
            consistency=sinetstream.EXACTLY_ONCE,  # not supported by umqtt
        )
        self._test_pubsub(kwargs, kwargs)

    ##################### test value_type
    def test_value_type_text(self):
        kwargs = dict(
            value_type="text"
        )
        self._test_pubsub(kwargs, kwargs, bytearrayp=False)

    def test_value_type_bytearray(self):
        kwargs = dict(
            value_type="byte_array"
        )
        self._test_pubsub(kwargs, kwargs, bytearrayp=True)

    @unittest.expectedFailure
    def test_value_type_invalid(self):
        kwargs = dict(
            value_type="invalid"  # invalid
        )
        self._test_pubsub(kwargs, kwargs)

    ##################### test data_compression
    from io import BytesIO
    import deflate
    has_deflating = hasattr(deflate.DeflateIO(BytesIO()), "write")

    @unittest.skipUnless(has_deflating, "DeflateIO built without deflating")
    def test_compression_on(self):
        kwargs = dict(
            data_compression=True
        )
        self._test_pubsub(kwargs, kwargs)

    def test_compression_off(self):
        kwargs = dict(
            data_compression=False
        )
        self._test_pubsub(kwargs, kwargs)

    ##################### test data_compression and compression
    @unittest.skipUnless(has_deflating, "DeflateIO built without deflating")
    def test_compression_on_gzip(self):
        kwargs = dict(
            data_compression=True,
            compression=dict(algorithm="gzip")
        )
        self._test_pubsub(kwargs, kwargs)

    @unittest.skipUnless(has_deflating, "DeflateIO built without deflating")
    def test_compression_on_gzip_level(self):
        kwargs = dict(
            data_compression=True,
            compression=dict(algorithm="gzip", level=1)
        )
        self._test_pubsub(kwargs, kwargs)

    @unittest.expectedFailure
    def test_compression_on_zstd(self):
        kwargs = dict(
            data_compression=True,
            compression=dict(algorithm="zstd")  # not supported
        )
        self._test_pubsub(kwargs, kwargs)

    ##################### test data_encryption
    def test_encryption_off(self):
        kwargs = dict(
            data_encryption=False,
        )
        self._test_pubsub(kwargs, kwargs)

    @unittest.skip("XXX NOT IMPLEMENTED")
    def test_encryption_on(self):
        kwargs = dict(
            data_encryption=True,
        )
        self._test_pubsub(kwargs, kwargs)

    ##################### test user_data_only
    def test_user_data_only_off(self):
        kwargs = dict(
            user_data_only=False,
        )
        self._test_pubsub(kwargs, kwargs)

    def test_user_data_only_on(self):
        kwargs = dict(
            user_data_only=True,
        )
        self._test_pubsub(kwargs, kwargs)

    @unittest.expectedFailure
    def test_user_data_only_mix(self):
        kwargs_on = dict(
            user_data_only=True,
        )
        kwargs_off = dict(
            user_data_only=False,
        )
        self._test_pubsub(kwargs_on, kwargs_off)  # reader fails decoding

    ##################### test use_realtime_clock and timestamp
    def test_use_realtime_clock_on(self):
        kwargs = dict(
            use_realtime_clock=True,
        )
        self._test_pubsub(kwargs, kwargs,
                          extraSub=lambda m: self.assertNotEqual(m.timestamp, 0))

    def test_use_realtime_clock_off(self):
        kwargs = dict(
            use_realtime_clock=False,
        )
        self._test_pubsub(kwargs, kwargs,
                          extraSub=lambda m: self.assertEqual(m.timestamp, 0))

    def test_use_realtime_clock_off_tstamp(self):
        kwargs = dict(
            use_realtime_clock=False,
        )
        tstamp = 1234
        self._test_pubsub(kwargs, kwargs,
                          kwargsPub={"timestamp": tstamp},
                          extraSub=lambda m: self.assertEqual(m.timestamp, tstamp))

    def test_use_realtime_clock_on_tstamp(self):
        kwargs = dict(
            use_realtime_clock=True,
        )
        tstamp = 1234
        self._test_pubsub(kwargs, kwargs,
                          kwargsPub={"timestamp": tstamp},
                          extraSub=lambda m: self.assertEqual(m.timestamp, tstamp))

    ##################### test clean_session
    def test_clean_session_on(self):
        kwargs = dict(
            type_spec=dict(
                clean_session=True,
            )
        )
        self._test_pubsub(kwargs, kwargs)

    def test_clean_session_off(self):
        kwargs = dict(
            type_spec=dict(
                clean_session=False,
            )
        )
        self._test_pubsub(kwargs, kwargs)

    @unittest.expectedFailure
    def test_clean_session_xxx(self):
        kwargs = dict(
            type_spec=dict(
                clean_session="abc",
            )
        )
        self._test_pubsub(kwargs, kwargs)

    ##################### test will
    def test_will(self):
        topic = gen_topic()
        m1 = gen_msg()
        will_topic = topic + "-will"
        will_payload = gen_msg()
        will_params = dict(
            topic=will_topic,
            payload=will_payload,
            value_type="text",
        )
        kwargs = dict(
            type_spec=dict(
                will=will_params
            )
        )
        with sinetstream.MessageReader(SERVICE, topic=will_topic) as will_rd:
            with sinetstream.MessageReader(SERVICE, topic=topic, **kwargs) as rd:
                with sinetstream.MessageWriter(SERVICE, topic=topic) as wr:
                    wr.publish(m1)
                    it = iter(rd)
                    m2 = next(it)
                    assert m2.value == m1
                rd._plugin._mqttc.sock.close()  # force shutdown
            will_it = iter(will_rd)
            will_m2 = next(will_it)
            assert will_m2.value == will_payload

    def test_will_retain(self):
        topic = gen_topic()
        m1 = gen_msg()
        will_topic = topic + "-will"
        will_payload = gen_msg()
        will_params = dict(
            topic=will_topic,
            payload=will_payload,
            value_type="text",
            retain=True
        )
        kwargs = dict(
            type_spec=dict(
                will=will_params
            )
        )
        with sinetstream.MessageReader(SERVICE, topic=topic, **kwargs) as rd:
            with sinetstream.MessageWriter(SERVICE, topic=topic) as wr:
                wr.publish(m1)
                it = iter(rd)
                m2 = next(it)
                assert m2.value == m1
            rd._plugin._mqttc.sock.close()  # force shutdown

        with sinetstream.MessageReader(SERVICE, topic=will_topic) as will_rd:
            will_it = iter(will_rd)
            will_m2 = next(will_it)
            assert will_m2.value == will_payload

    def test_will_qos(self):
        topic = gen_topic()
        m1 = gen_msg()
        will_topic = topic + "-will"
        will_payload = gen_msg()
        for qos in [0, 1, 2]:
            will_params = dict(
                topic=will_topic,
                payload=will_payload,
                value_type="text",
                qos=qos
            )
            kwargs = dict(
                type_spec=dict(
                    will=will_params
                )
            )
            with sinetstream.MessageReader(SERVICE, topic=will_topic) as will_rd:
                with sinetstream.MessageReader(SERVICE, topic=topic, **kwargs) as rd:
                    with sinetstream.MessageWriter(SERVICE, topic=topic) as wr:
                        wr.publish(m1)
                        it = iter(rd)
                        m2 = next(it)
                        assert m2.value == m1
                    rd._plugin._mqttc.sock.close()  # force shutdown
                will_it = iter(will_rd)
                will_m2 = next(will_it)
                assert will_m2.value == will_payload

    @unittest.expectedFailure
    def test_trasport(self):
        kwargs = dict(
            type_spec=dict(
                transport="websockets",  # not supported by umqtt
            ),
        )
        self._test_pubsub(kwargs, kwargs)

    @unittest.expectedFailure
    def test_keepalive(self):
        kwargs = dict(
            type_spec=dict(
                keepalive=1<<16, #too large
            ),
        )
        self._test_pubsub(kwargs, kwargs)

    def test_username(self):
        kwargs = dict(
            type_spec=dict(
                username_pw=dict(
                    username="alice",  # check log by eyeball
                    password="secret",
                ),
            ),
        )
        self._test_pubsub(kwargs, kwargs)

    def test_clean_session(self):
        for clean_session in [True, False]:
            kwargs = dict(
                type_spec=dict(
                    clean_session=clean_session
                ),
            )
            self._test_pubsub(kwargs, kwargs)

        """
        client_id = gen_client_id()
        topic = gen_topic()
        m1 = gen_msg()
        m2 = gen_msg()
        will_params = dict(
            topic=topic,
            payload=gen_msg(),
            value_type="text",
            retain=True,
        )
        with sinetstream.MessageReader(SERVICE, topic=topic) as rd:
            with sinetstream.MessageWriter(SERVICE, topic=topic, client_id=client_id, type_spec=dict(clean_session=True, will=will_params)) as wr:
                wr.publish(m1)
                it = iter(rd)
                r1 = next(it)
                assert r1.value == m1
                wr._plugin._mqttc.sock.close()  # force shutdown
            with sinetstream.MessageWriter(SERVICE, topic=topic, client_id=client_id, type_spec=dict(clean_session=False, will=will_params)) as wr:
                wr.publish(m2)
                it = iter(rd)
                r2 = next(it)
                self.assertEqual(r2.value, m2)
                assert r2.value == m2
        """

    def test_protocol(self):
        for protocol in ["MQTTv311"]:
            kwargs = dict(
                type_spec=dict(
                    protocol=protocol
                ),
            )
            self._test_pubsub(kwargs, kwargs)

    @unittest.expectedFailure
    def test_protocol_ng(self):
        for protocol in ["MQTTv31", "MQTTv5"]:
            kwargs = dict(
                type_spec=dict(
                    protocol=protocol
                ),
            )
            self._test_pubsub(kwargs, kwargs)

if __name__ == '__main__':
    #TestConfigParams().test_protocol_ng()
    unittest.main()
