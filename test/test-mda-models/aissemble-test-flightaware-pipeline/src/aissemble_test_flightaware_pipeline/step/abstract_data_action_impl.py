###
# #%L
# aiSSEMBLE::Test::MDA::FlightAware Pipeline
# %%
# Copyright (C) 2021 Booz Allen
# %%
# This software package is licensed under the Booz Allen Public License.
# All Rights Reserved. You may not copy, reproduce, distribute, publish,
# display, execute, modify, create derivative works of, transmit, sell or
# offer for resale, or in any way exploit any part of this solution without
# Booz Allen Hamilton's express written permission.
# #L%
###
from ..generated.step.abstract_data_action import AbstractDataAction
from krausening.logging import LogManager

class AbstractDataActionImpl(AbstractDataAction):
    """
    Contains the general concepts needed to perform a base aiSSEMBLE Reference Architecture Data Action.
    A Data Action is a step within a Data Flow. Business logic implemented in this class will be inherited by
    all Data Flow pipeline steps.

    GENERATED CODE - DO MODIFY.

    Generated from: templates/data-delivery-pyspark/abstract.data.action.impl.py.vm
    """

    logger = LogManager.get_instance().get_logger("AbstractDataActionImpl")


    def __init__(self, data_action_type, descriptive_label):
        super().__init__(data_action_type, descriptive_label)
