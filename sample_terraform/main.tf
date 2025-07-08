terraform {
  required_providers {
    local = {
      source = "hashicorp/local"
      version = ">= 2.0"
    }
  }
}

provider "local" {}

locals {
  set_disconnect_flow_flow_arn_set-disconnect-flow = "arn:aws:connect:eu-west-2:123456789012:instance/test-instance/contact-flow/test-disconnect-flow"
  get_queue_metrics_queue_arn_get-queue-metrics-queue = "arn:aws:connect:eu-west-2:123456789012:instance/test-instance/queue/test-queue"
  get_queue_metrics_agent_arn_get-queue-metrics-agent = "arn:aws:connect:eu-west-2:123456789012:instance/test-instance/agent/test-agent"
  create_task_flow_to_run_task_arn_create-task-manual = "arn:aws:connect:eu-west-2:123456789012:instance/test-instance/contact-flow/test-task-flow"
  create_task_set_references_key123_value_create-task-manual = "test-string-value"
  create_task_set_references_key456_value_create-task-manual = "test-email@example.com"
  loop_prompts_prompt_id_message1_loop-prompts = "arn:aws:connect:eu-west-2:123456789012:instance/test-instance/prompt/test-prompt-1"
  loop_prompts_prompt_id_message4_loop-prompts = "arn:aws:connect:eu-west-2:123456789012:instance/test-instance/prompt/test-prompt-4"
  send_message_template_arn_send-message-email = "arn:aws:connect:eu-west-2:123456789012:instance/test-instance/message-template/test-template"
  send_message_knowledge_base_arn_send-message-email = "arn:aws:connect:eu-west-2:123456789012:instance/test-instance/knowledge-base/test-kb"
  amazon_q_connect_domain_arn_amazon-q-connect = "arn:aws:connect:eu-west-2:123456789012:instance/test-instance/assistant/test-assistant"
  loop_prompts_s3_file_path_message2_loop-prompts = "s3://test-bucket/test-audio.wav"
  send_message_email_from_email_address_send-message-email-zaGelDUvnf = "test@example.com"
  send_message_template_arn_send-message-sms = "arn:aws:connect:eu-west-2:123456789012:instance/test-instance/message-template/test-sms-template"
  send_message_knowledge_base_arn_send-message-sms = "arn:aws:connect:eu-west-2:123456789012:instance/test-instance/knowledge-base/test-sms-kb"
  send_message_sms_flow_arn_send-message-sms-mqXNlFZpIh = "arn:aws:connect:eu-west-2:123456789012:instance/test-instance/contact-flow/test-sms-flow"
  set_event_flow_default_flow_for_agent_ui_arn_set-event-flow-default-flow-for-agent-UI = "arn:aws:connect:eu-west-2:123456789012:instance/test-instance/contact-flow/test-default-ui-flow"
  set_event_flow_disconnect_flow_for_agent_ui_arn_set-event-flow-disconnect-flow-for-agent-ui = "arn:aws:connect:eu-west-2:123456789012:instance/test-instance/contact-flow/test-disconnect-ui-flow"
  set_event_flow_flow_at_contact_resume_arn_set-event-flow-flow-at-contact-resume = "arn:aws:connect:eu-west-2:123456789012:instance/test-instance/contact-flow/test-resume-flow"
  set_event_flow_flow_at_contact_pause_arn_set-event-flow-flow-at-contact-pause = "arn:aws:connect:eu-west-2:123456789012:instance/test-instance/contact-flow/test-pause-flow"
  aws_lambda_function_function_arn_aws-lambda-function = "arn:aws:lambda:eu-west-2:123456789012:function:test-lambda-function"
  cases_case_template_id_cases-create-case = "test-case-template-id"
  customer_profiles_associate_contact_to_profile_profile_id_customer-profiles-associate-contact-to-profile = "test-profile-id"
  customer_profiles_associate_contact_to_profile_contact_id_customer-profiles-associate-contact-to-profile = "test-contact-id"
  customer_profiles_get_customer_profile_object_profile_id_customer-profiles-get-customer-profile = "test-profile-id"
  customer_profiles_get_calculated_attributes_profile_id_customer-profiles-get-calculated-attributes = "test-profile-id"
  customer_profiles_check_segment_membership_profile_id_customer-profiles-check-segment-membership = "test-profile-id"
  customer_profiles_check_segment_membership_segment_name_customer-profiles-check-segment-membership = "test-segment-name"
}

data "template_file" "connect_flow" {
  template = file("${path.module}/../flow_templates/agent_hold.tftpl")
  vars = {
    # Original variables
    set_disconnect_flow_flow_arn_set-disconnect-flow = local.set_disconnect_flow_flow_arn_set-disconnect-flow
    get_queue_metrics_queue_arn_get-queue-metrics-queue = local.get_queue_metrics_queue_arn_get-queue-metrics-queue
    get_queue_metrics_agent_arn_get-queue-metrics-agent = local.get_queue_metrics_agent_arn_get-queue-metrics-agent
    create_task_flow_to_run_task_arn_create-task-manual = local.create_task_flow_to_run_task_arn_create-task-manual
    create_task_set_references_key123_value_create-task-manual = local.create_task_set_references_key123_value_create-task-manual
    create_task_set_references_key456_value_create-task-manual = local.create_task_set_references_key456_value_create-task-manual
    loop_prompts_prompt_id_message1_loop-prompts = local.loop_prompts_prompt_id_message1_loop-prompts
    loop_prompts_prompt_id_message4_loop-prompts = local.loop_prompts_prompt_id_message4_loop-prompts
    send_message_template_arn_send-message-email = local.send_message_template_arn_send-message-email
    send_message_knowledge_base_arn_send-message-email = local.send_message_knowledge_base_arn_send-message-email
    amazon_q_connect_domain_arn_amazon-q-connect = local.amazon_q_connect_domain_arn_amazon-q-connect
    loop_prompts_s3_file_path_message2_loop-prompts = local.loop_prompts_s3_file_path_message2_loop-prompts
    send_message_email_from_email_address_send-message-email-zaGelDUvnf = local.send_message_email_from_email_address_send-message-email-zaGelDUvnf
    send_message_template_arn_send-message-sms = local.send_message_template_arn_send-message-sms
    send_message_knowledge_base_arn_send-message-sms = local.send_message_knowledge_base_arn_send-message-sms
    send_message_sms_flow_arn_send-message-sms-mqXNlFZpIh = local.send_message_sms_flow_arn_send-message-sms-mqXNlFZpIh
    set_event_flow_default_flow_for_agent_ui_arn_set-event-flow-default-flow-for-agent-UI = local.set_event_flow_default_flow_for_agent_ui_arn_set-event-flow-default-flow-for-agent-UI
    set_event_flow_disconnect_flow_for_agent_ui_arn_set-event-flow-disconnect-flow-for-agent-ui = local.set_event_flow_disconnect_flow_for_agent_ui_arn_set-event-flow-disconnect-flow-for-agent-ui
    set_event_flow_flow_at_contact_resume_arn_set-event-flow-flow-at-contact-resume = local.set_event_flow_flow_at_contact_resume_arn_set-event-flow-flow-at-contact-resume
    set_event_flow_flow_at_contact_pause_arn_set-event-flow-flow-at-contact-pause = local.set_event_flow_flow_at_contact_pause_arn_set-event-flow-flow-at-contact-pause
    aws_lambda_function_function_arn_aws-lambda-function = local.aws_lambda_function_function_arn_aws-lambda-function
    cases_case_template_id_cases-create-case = local.cases_case_template_id_cases-create-case
    customer_profiles_associate_contact_to_profile_profile_id_customer-profiles-associate-contact-to-profile = local.customer_profiles_associate_contact_to_profile_profile_id_customer-profiles-associate-contact-to-profile
    customer_profiles_associate_contact_to_profile_contact_id_customer-profiles-associate-contact-to-profile = local.customer_profiles_associate_contact_to_profile_contact_id_customer-profiles-associate-contact-to-profile
    customer_profiles_get_customer_profile_object_profile_id_customer-profiles-get-customer-profile = local.customer_profiles_get_customer_profile_object_profile_id_customer-profiles-get-customer-profile
    customer_profiles_get_calculated_attributes_profile_id_customer-profiles-get-calculated-attributes = local.customer_profiles_get_calculated_attributes_profile_id_customer-profiles-get-calculated-attributes
    customer_profiles_check_segment_membership_profile_id_customer-profiles-check-segment-membership = local.customer_profiles_check_segment_membership_profile_id_customer-profiles-check-segment-membership
    customer_profiles_check_segment_membership_segment_name_customer-profiles-check-segment-membership = local.customer_profiles_check_segment_membership_segment_name_customer-profiles-check-segment-membership
  }
}

resource "local_file" "rendered_flow" {
  content  = data.template_file.connect_flow.rendered
  filename = "${path.module}/../sample_outputted_flows/agent_hold_rendered.json"
}

output "rendered_flow_json" {
  value = data.template_file.connect_flow.rendered
} 