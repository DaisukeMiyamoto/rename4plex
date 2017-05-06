#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re


class RenameForPlex():
    def __init__(self, input_path, output_path, debug=False):
        self.broadcast_list = {'ATX':3, 'BS11':3, 'MX':-2}
        self.debug = debug

        self.input_path = input_path
        self.output_path = output_path
        self.title_list = self._get_title_list(self.input_path)
        self.checked_file_no = 0
        self.created_file_no = 0
        self.existed_file_no = 0
        self.created_dir_no = 0
        self.check_case_1_no = 0
        self.check_case_2_no = 0
        self.check_case_3_no = 0
        self.check_case_error_no = 0

        self.checked_title_no = len(self.title_list)

        season_pattern = r'[A-Za-z_0-9]+[A-Za-z_]+[1-9]$'
        self.season_re = re.compile(season_pattern)
        number_pattern = r'[0-9]+$'
        self.number_re = re.compile(number_pattern)
        postfix_pattern = r'(HD)|(CS)|(BSD)$'
        self.postfix_re = re.compile(postfix_pattern)


    @staticmethod
    def _get_title_list(input_path):
        title_list = os.listdir(input_path)
        return title_list

    def run(self):
        for title in self.title_list:
            if os.path.isdir(os.path.join(self.input_path, title)):
                episode_set = self._make_episode_set(title)
                self._make_links(title, episode_set)

    def _broadcast_priority(self, broadcast):
        priority = 0

        if broadcast in self.broadcast_list:
            priority = self.broadcast_list[broadcast]

        return priority

    def _check_season(self, name):
        if self.season_re.match(name):
            return int(name[-1])

        return 1

    def _check_name(self, name):
        """name rules
        TITLE.%d.BROADCAST.DATE.EXT
        TITLE.%02d.BROADCAST.DATE.EXT
        TITLE%dHD.EXT
        TITLE%dCS.EXT
        TITLE%02d.EXT
        TITLE%d.EXT
        :param name: 
        :return: 
        """
        self.checked_file_no += 1
        info = dict()
        # info['title'] = ''
        splitted_name = name.split('.')
        info['name'] = name
        info['basename'] = splitted_name[0]
        info['ext'] = splitted_name[-1]
        info['priority'] = 0

        if len(splitted_name) == 5 and splitted_name[1].isdigit():
            # CASE 1
            self.check_case_1_no += 1
            info['title'] = info['basename']
            info['no'] = int(splitted_name[1])
            info['broadcast'] = splitted_name[2]
            info['priority'] = 10 + self._broadcast_priority(info['broadcast'])

        elif len(splitted_name) == 2:
            # CASE 2
            self.check_case_2_no += 1
            if self.postfix_re.match(info['basename']):
                info['basename'] = self.postfix_re.sub('', info['basename'])
                info['priority'] += 1

            info['title'] = self.number_re.split(info['basename'])[0]
            if info['title'][-1] == '_':
                info['title'] = info['title'][:-1]

            no_list = self.number_re.findall(info['basename'])
            if len(no_list) == 0 or not no_list[0].isdigit():
                self.check_case_error_no += 1
                info['priority'] = 0
                return info
            else:
                info['no'] = int(no_list[0])
                info['priority'] += 1

        else:
            self.check_case_error_no += 1
            # print(name)
            # print('[%s] is not match' % str(name))
            return info

        info['season'] = int(self._check_season(info['title']))
        info['target'] = '%s_s%02d_e%03d' % (info['title'], info['season'], info['no'])
        return info

    def _make_episode_set(self, title):
        episode_set = dict()

        in_path = os.path.join(self.input_path, title)
        episode_list = os.listdir(in_path)
        if self.debug:
            print(episode_list)
        for file_name in episode_list:
            info = self._check_name(file_name)
            if self.debug:
                print(info)
            if info['priority'] <= 0:
                continue

            if info['target'] in episode_set:
                if info['priority'] > episode_set[info['target']]['priority']:
                    episode_set[info['target']] = info
            else:
                episode_set[info['target']] = info

        return episode_set

    def _make_links(self, title, episode_set):
        input_prefix = os.path.join(self.input_path, title)
        # output_prefix = os.path.join(self.output_path, title)

        for k, v in episode_set.items():
            if self.debug:
                print('%s -> %s' % (k, v['name'], ))

            output_prefix = os.path.join(self.output_path, v['title'])
            if not os.path.isdir(output_prefix):
                os.makedirs(output_prefix)
                self.created_dir_no += 1

            input_file_path = os.path.join(input_prefix, v['name'])
            output_file_path = os.path.join(output_prefix, k + '.' + v['ext'])
            if os.path.isfile(output_file_path):
                self.existed_file_no += 1
            else:
                os.symlink(input_file_path, output_file_path)
                self.created_file_no += 1

    def show_result(self):
        print('\n-----------------------------------------------')
        print(' [%s] -> [%s]' % (self.input_path, self.output_path))
        print(' * Checked Titles: %d' % self.checked_title_no)
        print(' * Checked Files: %d' % self.checked_file_no)
        print(' * Created Files: %d' % self.created_file_no)
        print(' * Existed Files: %d' % self.existed_file_no)
        print(' * Created Dirs: %d' % self.created_dir_no)
        print(' * Check Case 1: %d' % self.check_case_1_no)
        print(' * Check Case 2: %d' % self.check_case_2_no)
        print(' * Check Case Error: %d' % self.check_case_error_no)


def main():
    rfp = RenameForPlex(input_path='/share/backstores/tmp3/anime', output_path='/share/test_plex', debug=False)
    rfp.run()
    rfp.show_result()
    rfp = RenameForPlex(input_path='/share/backstores/tmp2/anime', output_path='/share/test_plex', debug=False)
    rfp.run()
    rfp.show_result()
    rfp = RenameForPlex(input_path='/share/backstores/tmp1/anime', output_path='/share/test_plex', debug=False)
    rfp.run()
    rfp.show_result()


if __name__ == '__main__':
    main()
