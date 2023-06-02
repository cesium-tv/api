<template>
  <v-container>
    <v-layout wrap>
      <v-flex sm12 md6 offset-md3>
        <v-card elevation="4" light tag="section">
          <v-card-title>
            <v-layout align-center justify-space-between>
              <h3 class="headline">
                Link your Device
              </h3>
              <v-flex>
                <v-img
                  contain
                  :alt="theme.name"
                  :src="theme.logo"
                  class="ml-3"
                  height="48px"
                  position="center right"
                ></v-img>
              </v-flex>
            </v-layout>
          </v-card-title>
          <v-card-subtitle>
            Allow your device to access your account and subscriptions
          </v-card-subtitle>
          <v-divider></v-divider>
          <v-card-text>
            <v-form>
              <v-layout row wrap class="mt-6 pb-6">
                <v-flex xs12 class="px-3">
                  <v-text-field
                    v-model="user_code"
                    label="User code"
                  ></v-text-field>
                  <v-checkbox
                    v-if="oauthInfo"
                    :error="Boolean(error)"
                    v-model="form.confirm"
                    value="true"
                  >
                    <template v-slot:label>
                      I authorize&nbsp;
                      <a
                        :href="oauthInfo.website_url"
                      >{{ oauthInfo.client_name }}</a>
                      &nbsp;to access my account
                    </template>
                  </v-checkbox>
                  <p
                    v-else
                  >Invalid user code</p>
                </v-flex>
              </v-layout>
            </v-form>
          </v-card-text>
          <v-divider></v-divider>
          <v-card-actions :class="{ 'pa-3': $vuetify.breakpoint.smAndUp }">
            <v-btn
              @click.cancel="onCancel"
              color="warning" large
            >
              <v-icon left>cancel</v-icon>
              Cancel
            </v-btn>
            <v-spacer></v-spacer>
            <v-btn
              @click="onVerify"
              color="info" large
            >
              <v-icon left>check</v-icon>
              Verify
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-flex>
    </v-layout>
  </v-container>
</template>

<script>
import axios from 'axios';

export default {
  name: 'Verify',

  data() {
    return {
      user_code: this.$route.query.user_code,
      theme: window.CesiumTheme,
      oauthInfo: null,
      error: null,
      form: {
        confirm: false,
      },
    };
  },

  mounted() {
    this.onUserCode(this.user_code);
  },

  watch: {
    user_code(newValue) {
      this.onUserCode(newValue);
    },
  },

  methods: {
    userCodeIsValid(user_code) {
      return (/\w{4}-\w{4}/.test(user_code));
    },

    onUserCode(user_code) {
      if (!this.userCodeIsValid(user_code)) {
        this.oauthInfo = null;
        return;
      }

      const params = {
        user_code: user_code,
      };

      axios
        .get('/api/v1/oauth2/device/verify/', { params })
        .then((r) => {
          this.oauthInfo = r.data;
        })
        .catch((/*e*/) => {
          this.oauthInfo = null;
          // console.error(e);
        });
    },

    onVerify() {
      const params = {
        params: {
            user_code: this.user_code
          },
      };

      axios
        .post('/api/v1/oauth2/device/verify/', this.form, params)
        .then(() => {
          this.$router.push('/');
        })
        .catch((e) => {
          if (e.response) {
            this.error = e.response.data.message;
          } else {
            this.error = e.message;
          }
          console.error(e);
        })
    },

    onCancel() {
      history.back();
    },
  },
}
</script>

<style scoped>

</style>