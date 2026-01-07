#!/usr/bin/env python3

# Copyright (C) 2019 National Institute of Informatics
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import logging
import socket
import ssl
from collections import OrderedDict
from math import inf
"""#if sinetstream-python
from queue import Queue, Empty
from sys import exc_info
from threading import Condition, Lock
"""#if sinetstream-upython
from collections import deque
#endif

"""#if sinetstream-python
from paho.mqtt.client import (
    Client, MQTT_ERR_QUEUE_SIZE, MQTT_ERR_NO_CONN,
    connack_string, MQTTv31, MQTTv311, MQTTv5, WebsocketConnectionError,
    MQTT_ERR_SUCCESS)
from paho.mqtt.properties import (Properties, MQTTException)
from paho.mqtt.packettypes import PacketTypes
from promise import Promise
"""#if sinetstream-upython
from umqtt.simple import MQTTClient
#endif

from sinetstream import (
    AT_MOST_ONCE, AT_LEAST_ONCE, EXACTLY_ONCE,
    InvalidArgumentError, ConnectionError,
    SinetError)

from sinetstream import SINETStreamMessageEncoder

logger = logging.getLogger(__name__)

#if sinetstream-upython
class Lock:
    def __enter__(self):
        pass
    def __exit__(self, _a, _b, _c):
        pass
class Condition:
    def __enter__(self):
        pass
    def __exit__(self, _a, _b, _c):
        pass
    def wait_for(self, _cond, _timeout):
        pass
    def notify_all(self):
        pass
#endif

QOS_MAP = {
    AT_MOST_ONCE: 0,
    AT_LEAST_ONCE: 1,
    EXACTLY_ONCE: 2,
    'AT_MOST_ONCE': 0,
    'AT_LEAST_ONCE': 1,
    'EXACTLY_ONCE': 2,
}


def _to_qos(comm_params, mqtt_params):
    qos = mqtt_params.get('qos')
    if qos is not None:
        if qos not in QOS_MAP.values():
            raise InvalidArgumentError('Invalid QoS level')
        return qos

    consistency = comm_params.get('consistency')
    if consistency is not None:
        assert consistency in QOS_MAP
        return QOS_MAP[consistency]

    return None


def _get_qos(comm_params):
    consistency = comm_params['consistency']
    return QOS_MAP[consistency]


class MqttReaderHandleIter:
    def __init__(self, reader):
        logger.debug("MqttReaderHandleIter:init")
        self._reader = reader

    def __next__(self):
        logger.debug("MqttReaderHandleIter:next")
        if self._reader is None:
            raise StopIteration()
        try:
            return self._reader.pop_rcvq()
            """#if sinetstream-python
        except Empty as ex:
            """#if sinetstream-upython
        except IndexError as ex:
            #endif
            self._reader = None
            raise StopIteration() from ex


def _get_broker(comm_params, mqtt_params):
    if 'brokers' not in comm_params:
        logger.error("You must specify one broker.")
        raise InvalidArgumentError("You must specify one broker.")

    brokers = comm_params["brokers"]
    if isinstance(brokers, list):
        if len(brokers) > 1:
            logger.error("only one broker can be specified")
            raise InvalidArgumentError("only one broker can be specified")
        elif len(brokers) == 0:
            logger.error("You must specify one broker.")
            raise InvalidArgumentError("You must specify one broker.")
        host_port = brokers[0].split(':', 1)
    else:
        host_port = brokers.split(':', 1)
    if len(host_port) == 2:
        return host_port[0], int(host_port[1])
    else:
        return host_port[0], _get_default_port(mqtt_params)


def _get_default_port(mqtt_params):
    """#if sinetstream-python
    transport = mqtt_params.get('transport')
    """#if sinetstream-upython
    transport = _get_transport(mqtt_params)
    #endif
    is_tls = 'tls_set' in mqtt_params # XXX FIXME

    if transport != 'websockets':
        return 1883 if not is_tls else 8883
    else:
        return 80 if not is_tls else 443


_MQTT_NESTED_PARAMETER = [
    ('max_inflight_messages', 'max_inflight_messages_set'),
    ('max_queued_messages',   'max_queued_messages_set'),
    ('message_retry',         'message_retry_set'),
    ('ws_options',            'ws_set_options'),
    ('tls',                   'tls_set'),
    ('tls_insecure',          'tls_insecure_set'),
    ('username_pw',           'username_pw_set'),
    ('will',                  'will_set'),
    ('reconnect_delay',       'reconnect_delay_set'),
]

# Nested parameters that paho-mqtt expects as str type
_MQTT_STRING_PARAMS = {
    'username_pw': ['username', 'password'],
    'username_pw_set': ['username', 'password'],  # CONFVER1 compatibility
}


def _conv_bytes_to_str(params):
    """Convert bytes to str for parameters that paho-mqtt expects as str."""
    for param_name, keys in _MQTT_STRING_PARAMS.items():
        if param_name not in params:
            continue
        nested = params[param_name]
        for key in keys:
            if key in nested and isinstance(nested[key], bytes):
                nested[key] = nested[key].decode('utf-8')


"""#if sinetstream-python
PROTOCOL_MAP = {
    'MQTTv31': MQTTv31,
    'MQTTv311': MQTTv311,
    'MQTTv5': MQTTv5,
    None: MQTTv311,
}
"""#if sinetstream-upython
MQTTv311 = None   #XXX dummy placeholder

PROTOCOL_MAP = {
    'MQTTv311': MQTTv311,
    None: MQTTv311,
}
#endif


def _to_protocol(protocol):
    if protocol not in PROTOCOL_MAP:
        raise InvalidArgumentError(f'protocol: invalid value: {protocol}')
    return PROTOCOL_MAP[protocol]


def _get_transport(mqtt_params):
    transport = mqtt_params.get('transport', 'tcp')
    """#if sinetstream-python
    if transport not in ['tcp', 'websockets']:
        raise InvalidArgumentError(f'transport: invalid value: {transport}')
    """#if sinetstream-upython
    if transport not in ['tcp']:
        raise InvalidArgumentError(f'transport: invalid value: {transport}')
    #endif
    return transport


def _create_mqtt_client(confver, comm_params, mqtt_params):
    logger.debug(f"_create_mqtt_client {comm_params=} {mqtt_params=}")
    """#if sinetstream-python
    mqttc = Client(
        client_id=comm_params.get("client_id", ''),
        clean_session=mqtt_params.get('clean_session'),  # NOTE: MUST be None in MQTTv5, USE clean_start
        protocol=_to_protocol(mqtt_params.get('protocol')),
        transport=_get_transport(mqtt_params),
        # reconnect_on_failure=mqtt_params.get("reconnect_on_failure", True),
    )
    """#endif

    _conv_bytes_to_str(mqtt_params)

    use_type_spec = confver.type_spec()
    """#if sinetstream-python
    for name3, method_name in _MQTT_NESTED_PARAMETER:
        name = name3 if use_type_spec else method_name
        if name not in mqtt_params:
            continue
        logger.debug(f'invoke: {method_name}(name={name},arg={mqtt_params[name]})')
        getattr(mqttc, method_name)(**mqtt_params[name])
    """#endif
    #if sinetstream-upython
    host, port = _get_broker(comm_params, mqtt_params)
    username_pw = mqtt_params.get("username_pw") if use_type_spec else \
                  comm_params.get("username_pw_set")
    username, password = (None, None) if username_pw is None else \
                         (username_pw.get("username"), username_pw.get("password"))
    keepalive_deault = 60
    keepalive = mqtt_params.get('keepalive', keepalive_deault) if use_type_spec else \
                comm_params.get('keepalive', keepalive_deault)
    mqttc = MQTTClient(client_id=comm_params.get("client_id", ''),
                       server=host,
                       port=port,
                       user=username,
                       password=password,
                       keepalive=keepalive, #XXX umqtt's default is 0
                       ssl=None) #XXX SSL is not implemented yet
    #endif

    """#if sinetstream-python
    mqttc.enable_logger(logger)
    """#endif
    return mqttc


def _translate_tls_params(comm_params, is_v1):
    key_tls = 'tls'
    key_tls_insecure = 'tls_insecure'
    if is_v1:
        key_tls += '_set'
        key_tls_insecure += '_set'

    tls = comm_params.get('tls')
    if tls is None:
        return {}
    elif isinstance(tls, bool):
        return {key_tls: {}}
    elif isinstance(tls, dict):
        tls_set = {key: tls[key]
                   for key in ['ca_certs', 'certfile', 'keyfile', 'ciphers']
                   if key in tls
                   }
        mqtt_params = {key_tls: tls_set}
        if 'check_hostname' in tls:
            mqtt_params[key_tls_insecure] = {
                'value': not (tls['check_hostname']),
            }
        return mqtt_params
    else:
        logger.error("tls: must be bool or associative array")
        raise InvalidArgumentError("tls: must be bool or associative array")


def _replace_ssl_params(mqtt_params, is_v1):
    key_tls = 'tls'
    if is_v1:
        key_tls += '_set'
    if key_tls not in mqtt_params:
        return
    mqtt_params[key_tls] = {
        key: (getattr(ssl, value)
              if (key in ['cert_reqs', 'tls_version'] and
                  isinstance(value, str) and
                  hasattr(ssl, value))
              else value)
        for key, value in mqtt_params[key_tls].items()
    }


def _replace_will_params(mqtt_params, is_v1):
    key_will = 'will'
    if is_v1:
        key_will += '_set'
    if key_will not in mqtt_params:
        return
    will_params = mqtt_params[key_will]

    for k in ['topic', 'payload']:
        if k not in will_params:
            raise InvalidArgumentError(f'the parameter {k} in will_set must be specified')

    if 'delay_interval' in will_params:
        props = Properties(PacketTypes.WILLMESSAGE)
        props.WillDelayInterval = will_params.pop('delay_interval')
        will_params['properties'] = props

    qos = _to_qos({}, will_params)
    if qos is not None:
        will_params['qos'] = qos
    will_params.pop('consistency', None)  # note: del will_params['consistency'] safely.

    args = ['topic', 'payload', 'qos', 'retain', 'properties']
    will_params2 = {k: will_params[k] for k in args if k in will_params}
    writer_params = {k: will_params[k] for k in will_params.keys() if k not in args}
    with SINETStreamMessageEncoder(**writer_params) as enc:
        payload = will_params['payload']
        will_params2['payload'] = enc.encode(payload, timestamp=0)

    mqtt_params[key_will] = will_params2


class MqttClient:
    def __init__(self, confver, params):
        if confver.type_spec():
            self._comm_params = params.copy()
            self._comm_params.pop("type_spec", None)
            self._mqtt_params = params.get("type_spec", {})
            self._mqtt_params.update(_translate_tls_params(self._comm_params, False))
            _replace_ssl_params(self._mqtt_params, False)
            _replace_will_params(self._mqtt_params, False)
        else:
            ps = _translate_tls_params(params, True)
            ps.update(params)
            self._comm_params = ps
            self._mqtt_params = ps
            _replace_ssl_params(self._mqtt_params, True)
            _replace_will_params(self._mqtt_params, True)
        logger.debug(self._comm_params)
        logger.debug(self._mqtt_params)

        try:
            self._mqttc = _create_mqtt_client(confver, self._comm_params, self._mqtt_params)
        except ValueError as ex:
            raise InvalidArgumentError(ex) from ex

        """#if sinetstream-python
        self._mqttc.on_connect = self._on_connect
        """#endif
        self.qos = _to_qos(self._comm_params, self._mqtt_params)
        """#if sinetstream-python
        self.connection_timeout = self._mqtt_params.get('connection_timeout', 10)
        """#endif
        self.keepalive = self._mqtt_params.get('keepalive', 60)
        self.host, self.port = _get_broker(self._comm_params, self._mqtt_params)
        logger.debug(f'broker={self.host} port={self.port}')
        self.protocol = _to_protocol(self._mqtt_params.get('protocol'))
        self._connection_result = None
        self._conn_cond = Condition()

        #if sinetstream-upython
        will_params = self._mqtt_params.get("will" if confver.type_spec() else "will_set")
        if will_params is not None:
            self._mqttc.set_last_will(
                    will_params["topic"],
                    will_params["payload"],
                    will_params.get("retain", False),
                    will_params.get("qos", 0))
        #endif

    """#if sinetstream-python
    def _make_properties(self):
        def name2(s):
            name = s.replace(" ", "")
            name_ = (s.replace("Information", "Info")
                      .replace("Authentication", "Auth")
                      .replace(" ", "_")
                      .lower())
            return (name, name_)
        properties = Properties(PacketTypes.CONNECT)
        n = 0
        for (name, name_) in [name2(k) for k in properties.names.keys()]:
            # print(f"name={name} name_={name_}")
            # ptype = PacketTypes.CONNECT
            # if ptype not in properties.properties[properties.getIdentFromName(name)][1]:
            #     continue
            if name_ in self._mqtt_params:
                n += 1
                val = self._mqtt_params[name_]
                if name_ == "user_property":
                    val = [(k, v) for k, v in val.items()]
                try:
                    setattr(properties, name, val)
                except MQTTException as ex:
                    # ok, maybe packet type mismatch.
                    logger.warning(f"{name_}: {ex}")
        logger.debug(f"properties={properties}")
        return properties if n > 0 else None
    """#endif

    def open(self, timeout=None):
        logger.debug("open")
        try:
            kwargs = {
                "host": self.host,
                "port": self.port,
                "keepalive": self.keepalive,
            }
            if "clean_start" in self._mqtt_params:
                kwargs["clean_start"] = self._mqtt_params["clean_start"]
            """#if sinetstream-python
            properties = self._make_properties()
            if properties is not None:
                kwargs["properties"] = properties
            self._mqttc.connect(**kwargs)
            """#if sinetstream-upython
            self._mqttc.connect(clean_session=self._mqtt_params.get("clean_session", True))
            #endif
            """#if sinetstream-python
        except (socket.error, OSError, WebsocketConnectionError, ValueError) as ex:
            logger.error(f"cannot connect broker: {self.host}:{self.port}", exc_info=True)
            """#endif
            #if sinetstream-upython
        except (OSError, ValueError) as ex:
            logger.error(f"cannot connect broker: {self.host}:{self.port}: {ex}")
            #endif
            self.close()
            raise ConnectionError(
                f"cannot connect broker: {self.host}:{self.port}") from ex

        """#if sinetstream-python
        self._mqttc.loop_start()
        """#if sinetstream-upython
        return self  # XXX umqtt's connect is blocking api.
        #endif

        """#if sinetstream-python
        if timeout is None:
            timeout = self.connection_timeout
        with self._conn_cond:
            ret = self._conn_cond.wait_for(self._is_connected, timeout)
            if not ret:
                self.close()
                raise ConnectionError('connection timed out')
            if self._connection_result != 0:
                if self.protocol == MQTTv5:
                    reason = str(self._connection_result)
                else:
                    reason = connack_string(self._connection_result)
                self.close()
                raise ConnectionError(f'connection error: reason={reason}')
        return self
        """#endif

    def close(self):
        logger.debug("close")
        try:
            self._mqttc.disconnect()
            """#if sinetstream-python
            self._mqttc.loop_stop()
            """#endif
            """#if sinetstream-python
        except Exception:
            logger.error("mqtt close() error", exc_info=True)
            """#if sinetstream-upython
        except Exception as ex:
            logger.error(f"mqtt close() error: {ex}")
            #endif

    #if sinetstream-upython
    def pingpong(self):
        self._mqttc.ping()
        self._mqttc.wait_msg()

    def ping(self):
        self._mqttc.ping()
    #endif

    def metrics(self):
        return None

    def reset_metrics(self):
        pass

    def _is_connected(self):
        return self._connection_result is not None

    """#if sinetstream-python
    def _on_connect(self, _client, _userdata, _flags, rc, _properties=None):
        logger.debug(f"MQTT:on_connect: rc={rc}")
        if rc != 0:
            logger.error(f"MQTT: {connack_string(rc)}: {rc}")
        with self._conn_cond:
            self._connection_result = rc
            self._conn_cond.notify_all()
    """#endif

    def _debug_get_socket(self):
        return self._mqttc.socket()


class BaseMqttReader(MqttClient):
    def __init__(self, confver, params):
        super().__init__(confver, params)
        self.topics = self._get_topics()
        timeout_ms = self._comm_params["receive_timeout_ms"]
        self._timeout = timeout_ms / 1000.0 if timeout_ms != inf else None

    def _get_topics(self):
        topics = self._comm_params.get('topics', [])
        return topics if isinstance(topics, list) else [topics]

    """#if sinetstream-python
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        super()._on_connect(client, userdata, flags, rc, properties)
        for topic in self.topics:
            client.subscribe(topic, self.qos)
    """#endif


class MqttReader(BaseMqttReader):
    #if sinetstream-upython
    qmaxlen = 1 # XXX tekito
    qflag = 1 # check overflow
    #endif

    def __init__(self, confver, params):
        logger.debug("MqttReader:init")
        super().__init__(confver, params)
        """#if sinetstream-python
        self._rcvq = Queue()
        self._mqttc.on_message = self._on_message
        """#if sinetstream-upython
        self._rcvq = deque([], self.qmaxlen, self.qflag)
        self._mqttc.set_callback(self._on_message)
        #endif

    #if sinetstream-upython
    def open(self, timeout=None):
        logger.debug("open")
        super().open(timeout)
        for topic in self.topics:
            self._mqttc.subscribe(topic, self.qos)
    #endif

    """#if sinetstream-python
    def _on_message(self, _client, _userdata, message):
        logger.debug(f"MQTT:on_message: message={message}")
        self._rcvq.put(message)
    """#if sinetstream-upython
    def _on_message(self, topic, msg):
        self._rcvq.append((topic, msg))
    #endif

    #if sinetstream-upython
    def _dump_mqtthdr(self, rc):
        typ = rc >> 4
        dup = (rc & (1<<3)) != 0
        qos = (rc >> 1) & 3
        retain = rc &1
        mne = {
            1: "CONNECT",
            2: "CONNACK",
            3: "PUBLISH",
            4: "PUBACK",
            5: "PUBREC",
            6: "PUBREL",
            7: "PUBCOMP",
            8: "SUBSCRIBE",
            9: "SUBACK",
            10: "UNSUBSCRIBE",
            11: "UNSUBACK",
            12: "PINGREQ",
            13: "PINGRESP",
            14: "DISCONNECT",
        }
        return f"mqtthdr(type={mne[typ]}, dup={dup}, qos={qos} retain={retain}"
    #endif

    def pop_rcvq(self):
        """#if sinetstream-python
        message = self._rcvq.get(block=True, timeout=self._timeout)
        return message.payload, message.topic, message
        """#if sinetstream-upython
        while (rc := self._mqttc.wait_msg()) == None:
            # memo: wait_msg returns None when recv PINGRESP
            # memo: wait_msg raises OSError(-1) when connection is closed
            pass
        logger.debug(f"wait_msg => {rc}")
        message = self._rcvq.popleft() # FIXME
        topic, payload = message
        return payload, topic, message
        #endif

    def __iter__(self):
        assert self._mqttc is not None
        return MqttReaderHandleIter(self)

"""#if sinetstream-python
class MqttAsyncReader(BaseMqttReader):
    def __init__(self, confver, params):
        logger.debug("MqttAsyncReader:init")
        super().__init__(confver, params)
        self._mqttc.on_message = self._mqtt_callback
        self._on_message = None

    def _mqtt_callback(self, _client, _userdata, message):
        logger.debug(f"MQTT:on_message: message={message}")
        if self._on_message is not None:
            self._on_message(message.payload, message.topic, message)

    @property
    def on_message(self):
        return self._on_message

    @on_message.setter
    def on_message(self, on_message):
        self._on_message = on_message

    @property
    def on_failure(self):
        pass
"""#endif


class BaseMqttWriter(MqttClient):
    def __init__(self, confver, params):
        logger.debug("MqttWriter:init")
        super().__init__(confver, params)
        self.topic = self._comm_params['topic']
        self.retain = self._mqtt_params.get('retain', False)

    def publish(self, msg):
        if not isinstance(msg, bytes):
            logger.error("MqttWriter: msg must be bytes")
            raise InvalidArgumentError("MqttWriter: msg must be bytes")
        """#if sinetstream-python
        return self._mqttc.publish(
            self.topic, payload=msg, qos=self.qos, retain=self.retain)
        """#if sinetstream-upython
        return self._mqttc.publish(
            self.topic, msg=msg, qos=self.qos, retain=self.retain)
        #endif


class MqttWriter(BaseMqttWriter):
    def __init__(self, confver, params):
        super().__init__(confver, params)

    def publish(self, msg):
        """#if sinetstream-python
        msg_info = super().publish(msg)
        if msg_info.rc != MQTT_ERR_QUEUE_SIZE:
            msg_info.wait_for_publish()
        elif msg_info.rc == MQTT_ERR_NO_CONN:
            raise ConnectionError('client is not currently connected')
        return msg_info
        """#if sinetstream-upython
        super().publish(msg)
        #endif


"""#if sinetstream-python
class MqttAsyncWriter(BaseMqttWriter):
    def __init__(self, confver, params):
        super().__init__(confver, params)
        self._callbacks = OrderedDict()
        self._lock = Lock()
        self._mqttc.on_publish = self._on_publish

    def publish(self, msg):
        msg_info = super().publish(msg)

        def executor(resolve, reject):
            if msg_info.rc == MQTT_ERR_NO_CONN:
                reject(ConnectionError('client is not currently connected'))
            try:
                if msg_info.is_published():
                    resolve(msg_info)
                elif msg_info.rc != MQTT_ERR_SUCCESS:
                    reject(SinetError(f'mqtt error: rc={msg_info.rc}'))
                else:
                    self._add_on_publish(msg_info, resolve)
            except Exception as ex:
                tb = exc_info()[2]
                reject(ex, tb)

        return Promise(executor)

    def _on_publish(self, _client, _userdata, mid):
        cb = self._callbacks.pop(mid, None)
        if cb is not None:
            cb[0](cb[1])

    def _add_on_publish(self, msg_info, callback):
        with self._lock:
            self._callbacks[msg_info.mid] = (callback, msg_info)
"""#endif
